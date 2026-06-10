# 🐛 Hugging Face Spaces - Startup Hang Troubleshooting Guide

## 🔍 Root Cause Analysis

### **CRITICAL ISSUE FOUND:**

**Location:** `app.py` lines 13-66 (`initialize_database()` and module-level call)

**Problem:** The `initialize_database()` function is called **at module import time** (line 66), **BEFORE** `st.set_page_config()`. This causes:

1. **Blocking initialization** - SQLite operations run before Streamlit starts
2. **No UI rendering** - Streamlit never gets a chance to render health check endpoint
3. **Hugging Face timeout** - Health check fails because app never becomes "ready"

### **Severity: 🔴 CRITICAL - BLOCKS DEPLOYMENT**

---

## 🚨 Issues Identified

### **1. Module-Level Database Initialization (CRITICAL)**

**File:** `app.py`, line 66

```python
# ❌ PROBLEM: Runs during import, blocks Streamlit startup
initialize_database()

# This executes BEFORE Streamlit can start its server
# Hugging Face health check never sees the app as "ready"
```

**Impact:**
- Blocks for 5-30 seconds during database setup
- Prevents Streamlit from responding to health checks
- Causes "Launch timed out" error

**Fix:** Move to inside a function that runs AFTER Streamlit starts

---

###  **2. Agent Creation at Import Time (HIGH)**

**File:** `shopping_agent.py`, lines 86-104, 566-577

```python
# ❌ PROBLEM: Creates ChatGroq and LangGraph agent during import
api_key = get_api_key()  # Calls st.secrets during import

llm = ChatGroq(...)  # HTTP connection to GROQ at import time
vision_llm = ChatGroq(...)  # Another HTTP connection

# Later...
agent = create_react_agent(...)  # Heavy initialization at import
```

**Impact:**
- Network requests during import (slow, can timeout)
- Agent creation before any user interaction needed
- `st.secrets` access before Streamlit is ready

**Fix:** Lazy initialization - create agent only when first needed

---

### **3. SentenceTransformer Model Loading (MEDIUM)**

**File:** `vector_search.py`, lines 44-66

```python
# ⚠️ WARNING: Downloads 80MB model when first called
def get_model():
    _model = SentenceTransformer(MODEL_NAME)  # Downloads on first call
```

**Impact:**
- 30-60 second download on first semantic search
- Model loads during user interaction (already lazy ✅)
- Can timeout if triggered too early

**Current Status:** ✅ Already lazy (only loads when `_ensure_embeddings_ready()` is called)

---

### **4. Import-Time Checkpointer Creation (LOW)**

**File:** `shopping_agent.py`, lines 558-565

```python
# ⚠️ MINOR: SQLite connection during import
checkpointer = SqliteSaver.from_conn_string(DB_PATH)
```

**Impact:**
- Opens database connection at import time
- Not critical but adds to startup delay

**Fix:** Move inside lazy function

---

## ✅ What's Already Fixed

1. ✅ **Lazy embedding generation** - `_ensure_embeddings_ready()` in app.py (line 509)
2. ✅ **Streamlit model caching** - `@st.cache_resource` in vector_search.py (line 51)
3. ✅ **No sync embedding build in setup_db.py** - Already removed

---

## 🔧 Required Fixes

### **Fix 1: Defer Database Initialization** (CRITICAL)

**Problem:** `initialize_database()` runs at module level before Streamlit starts

**Solution:** Wrap in lazy initializer that runs after first interaction

**File:** `app.py`

```python
# REMOVE THIS LINE (line 66):
# initialize_database()  # ❌ DON'T DO THIS

# ADD AFTER line 509 (_ensure_embeddings_ready function):

def _ensure_database_ready() -> bool:
    """
    Ensure database exists before processing requests.
    Runs once per session, cached in st.session_state.
    """
    if st.session_state.get("_database_ready"):
        return True
    
    db_path = os.path.join(os.path.dirname(__file__), "store.db")
    
    if not os.path.exists(db_path):
        # Database doesn't exist - create it
        try:
            import setup_db
            with st.spinner("⚙️ Setting up database..."):
                setup_db.create_database()
            st.session_state["_database_ready"] = True
            return True
        except Exception as e:
            st.error(f"❌ Database setup failed: {e}")
            return False
    else:
        # Database exists
        st.session_state["_database_ready"] = True
        return True

# THEN UPDATE initialize_session_state() to call it (after line 531):
def initialize_session_state() -> None:
    """Initialize all session state variables."""
    # ... existing code ...
    
    # Ensure database is ready
    _ensure_database_ready()
```

**Result:** Database initialization only runs when user first loads the page (after Streamlit is ready)

---

### **Fix 2: Lazy Agent Creation** (HIGH)

**Problem:** Agent created at module import time in `shopping_agent.py`

**Solution:** Create agent only when first needed

**File:** `shopping_agent.py`

```python
# REMOVE THESE LINES (88-104):
# api_key = get_api_key()
# llm = ChatGroq(...)
# vision_llm = ChatGroq(...)

# REMOVE THESE LINES (558-577):
# checkpointer = ...
# agent = create_react_agent(...)

# REPLACE WITH:

_agent = None
_llm = None
_vision_llm = None
_checkpointer = None

def get_llm():
    """Lazy load the LLM."""
    global _llm
    if _llm is None:
        api_key = get_api_key()
        _llm = ChatGroq(
            model="qwen/qwen3-32b",
            temperature=0,
            max_retries=3,
            api_key=api_key
        )
    return _llm

def get_vision_llm():
    """Lazy load the vision LLM."""
    global _vision_llm
    if _vision_llm is None:
        api_key = get_api_key()
        _vision_llm = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0,
            max_retries=3,
            api_key=api_key
        )
    return _vision_llm

def get_agent():
    """Lazy load the agent."""
    global _agent, _checkpointer
    if _agent is None:
        llm = get_llm()
        
        # Initialize checkpointer if enabled
        if config.ENABLE_CHECKPOINTING and CHECKPOINTING_AVAILABLE:
            try:
                from langgraph.checkpoint.sqlite import SqliteSaver
                _checkpointer = SqliteSaver.from_conn_string(DB_PATH)
            except Exception:
                _checkpointer = None
        
        # Create agent
        if _checkpointer:
            _agent = create_react_agent(
                model=llm,
                tools=ALL_TOOLS,
                checkpointer=_checkpointer,
                state_modifier=AGENT_SYSTEM_PROMPT
            )
        else:
            _agent = create_react_agent(
                model=llm,
                tools=ALL_TOOLS,
                state_modifier=AGENT_SYSTEM_PROMPT
            )
    return _agent

# UPDATE MODULE-LEVEL EXPORTS:
agent = get_agent  # Export function, not instance

# UPDATE describe_product_image tool to use lazy loading:
@tool
def describe_product_image(image_path: str) -> str:
    vision_llm = get_vision_llm()  # Lazy load here
    # ... rest of code ...
```

**File:** `app.py`

```python
# UPDATE IMPORT (line 13):
from shopping_agent import get_agent, set_user_context

# UPDATE process_agent_response function (around line 757):
def process_agent_response(messages: list) -> str:
    set_user_context(user_id)
    agent = get_agent()  # Lazy load
    result = agent().invoke(...)  # Call function to get instance
    return result["messages"][-1].content.replace("`", "")
```

**Result:** Agent only created when user first sends a message

---

### **Fix 3: Add Debug Logging** (RECOMMENDED)

**Add to `app.py` at the very top (after imports):**

```python
import sys
import time

# Debug: Track startup time
_startup_time = time.time()

def log_startup(message: str):
    """Log startup events with timestamp."""
    elapsed = time.time() - _startup_time
    print(f"[{elapsed:.2f}s] {message}", file=sys.stderr, flush=True)

log_startup("🚀 App module loading started")

# After each major section:
log_startup("✓ Imports complete")
log_startup("✓ st.set_page_config() called")
log_startup("✓ CSS loaded")
log_startup("✓ Functions defined")
log_startup("✓ Ready for user interaction")
```

**Result:** You'll see exactly where the app hangs in Hugging Face logs

---

## 🎯 Optimized Hugging Face Version

### **Complete app.py Fix:**

```python
"""
Professional AI Shopping Assistant
A production-grade intelligent shopping platform with visual search capabilities.
"""

import os
import sqlite3
import tempfile
from typing import Optional
import sys
import time

import streamlit as st

# Debug logging
_startup_time = time.time()
def log_startup(msg: str):
    print(f"[{time.time() - _startup_time:.2f}s] {msg}", file=sys.stderr, flush=True)

log_startup("🚀 Module loading")

from shopping_agent import get_agent, set_user_context
from auth_ui import render_auth_page, render_profile_modal, render_password_modal, render_orders_modal
from auth_manager import AuthManager
from memory_manager import MemoryManager
from config import ENABLE_AUTH, ENABLE_MEMORY

log_startup("✓ Imports complete")

# ==============================================================================
# Application Configuration (MUST BE FIRST STREAMLIT CALL)
# ==============================================================================

st.set_page_config(
    page_title="ShopWise AI | Intelligent Shopping Assistant",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-org/shopwise',
        'Report a bug': "https://github.com/your-org/shopwise/issues",
        'About': "ShopWise AI - Your intelligent shopping companion powered by advanced AI"
    }
)

log_startup("✓ st.set_page_config() called")

# ==============================================================================
# Custom CSS Styling
# ==============================================================================

st.markdown("""...""", unsafe_allow_html=True)

log_startup("✓ CSS loaded")

# ==============================================================================
# Lazy Initializers
# ==============================================================================

def _ensure_database_ready() -> bool:
    """Ensure database exists. Runs once per session."""
    if st.session_state.get("_database_ready"):
        return True
    
    db_path = os.path.join(os.path.dirname(__file__), "store.db")
    
    if not os.path.exists(db_path):
        try:
            import setup_db
            with st.spinner("⚙️ Setting up database..."):
                setup_db.create_database()
            st.session_state["_database_ready"] = True
            return True
        except Exception as e:
            st.error(f"❌ Database setup failed: {e}")
            return False
    else:
        st.session_state["_database_ready"] = True
        return True

def _ensure_embeddings_ready() -> bool:
    """Lazy build embeddings. Runs once per session."""
    # ... existing code ...

# ==============================================================================
# Session State Initialization
# ==============================================================================

def initialize_session_state() -> None:
    """Initialize all session state variables."""
    # ... existing code ...
    
    # Ensure database ready
    _ensure_database_ready()

# ... rest of file ...

log_startup("✓ Ready for user interaction")
```

---

## 📊 Expected Behavior After Fixes

### **Streamlit Logs (Hugging Face):**

```
[0.05s] 🚀 Module loading
[0.15s] ✓ Imports complete
[0.18s] ✓ st.set_page_config() called
[0.25s] ✓ CSS loaded
[0.30s] ✓ Functions defined
[0.35s] ✓ Ready for user interaction

===== Application Startup at 2024-XX-XX =====

You can now view your Streamlit app in your browser.
URL: http://0.0.0.0:7860

[Health check: PASS]
```

### **User First Visit:**
1. Page loads instantly (0.5s)
2. User clicks "Continue as Guest"
3. Database initializes (5s) - shows spinner
4. User types message
5. Agent creates (2s) - invisible to user
6. Embeddings build if needed (30-60s) - shows spinner

### **Subsequent Visits:**
1. Page loads instantly (0.5s)
2. Everything cached
3. Immediate interaction

---

## 🐛 Debug Checklist

Before deploying to Hugging Face, verify:

- [ ] No `initialize_database()` call at module level
- [ ] No agent creation outside functions
- [ ] No LLM instantiation at import time
- [ ] `st.set_page_config()` is first Streamlit call
- [ ] Debug logging added
- [ ] Test locally: `streamlit run app.py` starts in <1s

---

## 🔍 How to Debug on Hugging Face

### **1. Check Container Logs:**
- Go to your Space settings
- Click "Logs" tab
- Look for debug timestamps:
  - If logs stop before `[0.35s] ✓ Ready` → import-time blocking
  - If logs show `[30.00s+]` → timeout during initialization

### **2. Add More Debug Points:**
```python
log_startup(f"Importing shopping_agent...")
from shopping_agent import ...
log_startup(f"✓ shopping_agent imported")
```

### **3. Test Minimal Version:**
Create `app_minimal.py`:
```python
import streamlit as st
st.set_page_config(title="Test")
st.write("If you see this, Streamlit works!")
```

Deploy this first to verify infrastructure works.

---

## ✅ Summary

**Root Cause:** Database initialization and agent creation running **before** Streamlit starts

**Critical Fixes:**
1. Remove module-level `initialize_database()` call
2. Lazy load agent (`get_agent()` function)
3. Lazy load LLMs (`get_llm()` functions)

**Expected Result:** App starts in <1 second, passes health check, initializes on user interaction

**Deploy Priority:**
1. Fix #1 (database) - **CRITICAL**
2. Add debug logging - **HIGH**
3. Fix #2 (agent) - **HIGH**
4. Test and iterate

---

**Ready to fix? Apply changes in order and redeploy!** 🚀
