"""
Professional AI Shopping Assistant
A production-grade intelligent shopping platform with visual search capabilities.
"""

import os
import sqlite3
import tempfile
from typing import Optional

import streamlit as st

# ==============================================================================
# Application Configuration
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


from shopping_agent import agent, set_user_context
from auth_ui import render_auth_page, render_profile_modal, render_password_modal, render_orders_modal
from auth_manager import AuthManager
from memory_manager import MemoryManager
from config import ENABLE_AUTH, ENABLE_MEMORY

# ==============================================================================
# Database Initialization
# ==============================================================================

def initialize_database():
    """Initialize database if it doesn't exist or is empty."""
    db_path = os.path.join(os.path.dirname(__file__), "store.db")
    
    # Check if database exists and has data
    needs_init = False
    
    if not os.path.exists(db_path):
        needs_init = True
        st.info("🔄 Initializing database for first time...")
    else:
        # Check if product_embeddings table is empty
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM product_embeddings")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count == 0:
                needs_init = True
                st.info("🔄 Building product embeddings...")
        except sqlite3.OperationalError:
            # Table doesn't exist
            needs_init = True
            st.info("🔄 Setting up database tables...")
    
    if needs_init:
        with st.spinner("Setting up database... This may take a minute on first run."):
            try:
                # Import and run setup
                import setup_db
                setup_db.create_database()  # ✅ Correct function name
                st.success("✅ Database initialized successfully!")
            except Exception as e:
                st.error(f"❌ Database initialization failed: {e}")
                st.stop()




# Run database initialization before anything else
initialize_database()

# ==============================================================================
# Custom CSS Styling
# ==============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap');

:root {
  --bg: #ffffff;
  --bg-surface: #f8f9fa;
  --bg-card: #ffffff;
  --border: #e5e7eb;
  --border-hover: #9ca3af;
  --text-primary: #111827;
  --text-secondary: #6b7280;
  --text-muted: #9ca3af;
  --accent: #059669;
  --accent-light: #ecfdf5;
  --accent-hover: #047857;
  --warning: #d97706;
  --danger: #dc2626;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.04);
  --r-sm: 8px;
  --r-md: 12px;
  --r-lg: 20px;
  --font-display: 'Playfair Display', serif;
  --font-ui: 'IBM Plex Sans', sans-serif;
}

/* ── Base ── */
#MainMenu, footer, header, .stDeployButton { display: none !important; }

.stApp {
  background: var(--bg) !important;
  font-family: var(--font-ui);
  color: var(--text-primary);
}

.block-container {
  padding: 2.5rem 3rem 6rem !important;
  max-width: 1200px !important;
}

/* ── Typography ── */
h1, h2, h3 {
  font-family: var(--font-display) !important;
  color: var(--text-primary) !important;
  font-weight: 600 !important;
  letter-spacing: -0.02em;
}
h1 { font-size: 2.5rem !important; line-height: 1.2 !important; }
h2 { font-size: 1.875rem !important; }
h3 { font-size: 1.5rem !important; }

p, div { color: var(--text-primary) !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--bg-card) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
[data-testid="stSidebar"] hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* Sidebar section headers */
[data-testid="stSidebar"] .stMarkdown h3 {
  font-family: var(--font-ui) !important;
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-secondary) !important;
  margin-bottom: 1rem !important;
}

/* Profile card inside sidebar */
[data-testid="stSidebar"] .profile-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--shadow-sm);
}

/* ── Buttons ── */
/* Primary */
.stButton button[kind="primary"], button[kind="primary"] {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: var(--r-sm) !important;
  font-family: var(--font-ui) !important;
  font-weight: 600 !important;
  font-size: 0.9375rem !important;
  padding: 0.625rem 1.25rem !important;
  transition: all 0.15s ease !important;
  box-shadow: var(--shadow-sm) !important;
}
.stButton button[kind="primary"]:hover {
  background: var(--accent-hover) !important;
  transform: translateY(-1px);
  box-shadow: var(--shadow-md) !important;
}

/* Secondary / default */
.stButton button:not([kind="primary"]) {
  background: var(--bg-card) !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-sm) !important;
  font-family: var(--font-ui) !important;
  font-weight: 500 !important;
  font-size: 0.9375rem !important;
  transition: all 0.15s ease !important;
}
.stButton button:not([kind="primary"]):hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  transform: translateY(-1px);
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
  font-size: 0.9375rem !important;
  padding: 0.625rem 0.875rem !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-light) !important;
  outline: none !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
  color: var(--text-muted) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--border);
  gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border-radius: 0 !important;
  font-family: var(--font-ui) !important;
  font-size: 0.9375rem !important;
  font-weight: 500 !important;
  color: var(--text-muted) !important;
  padding: 0.875rem 1.75rem !important;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.15s ease;
}
.stTabs [aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom: 2px solid var(--accent) !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: transparent !important;
  padding: 1.75rem 0 0 !important;
}

/* ── Chat messages ── */
.stChatMessage {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  padding: 1.25rem 1.5rem !important;
  margin-bottom: 1rem !important;
  box-shadow: var(--shadow-sm);
  animation: msgIn 0.2s ease;
}
.stChatMessage[data-testid*="user"] {
  background: var(--bg-card) !important;
  border-left: 3px solid var(--accent) !important;
}
.stChatMessage[data-testid*="assistant"] {
  background: var(--bg-surface) !important;
  border-left: 3px solid var(--border) !important;
}
[data-testid="stChatMessageContent"] {
  font-family: var(--font-ui);
  font-size: 0.9375rem;
  line-height: 1.7;
  color: var(--text-primary);
}

/* ── Chat input ── */
.stChatInput textarea {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
  padding: 0.75rem 1rem !important;
}
.stChatInput textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-light) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
  background: var(--bg-card) !important;
  border: 1.5px dashed var(--accent) !important;
  border-radius: var(--r-md) !important;
  padding: 1.5rem !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
  font-weight: 500 !important;
}
.streamlit-expanderContent {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  color: var(--text-primary) !important;
}

/* ── Popover ── */
[data-testid="stPopover"] > div {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  box-shadow: 0 8px 30px rgba(0,0,0,0.12) !important;
}

/* ── Alerts ── */
.stAlert {
  background: var(--bg-card) !important;
  border-radius: var(--r-sm) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
}
div[data-baseweb="notification"] { border-radius: var(--r-sm) !important; }

/* ── Progress (password strength) ── */
.stProgress > div > div {
  background: #e5e7eb !important;
  border-radius: 99px !important;
}
.stProgress > div > div > div {
  border-radius: 99px !important;
  transition: width 0.3s ease, background-color 0.3s ease !important;
}

/* ── Checkbox ── */
.stCheckbox label { color: var(--text-primary) !important; font-family: var(--font-ui) !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── Divider ── */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 1.5rem 0 !important;
}

/* ── Utility classes (used in HTML strings) ── */
.sw-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  font-family: var(--font-ui);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.sw-badge-emerald  { background: var(--accent-light); color: var(--accent); border: 1px solid #bbf7d0; }
.sw-badge-warning { background: #fef3c7; color: var(--warning); border: 1px solid #fde68a; }

.sw-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}
.sw-card:hover { border-color: var(--border-hover); transform: translateY(-1px); box-shadow: var(--shadow-md); }

.sw-stat-num {
  font-family: var(--font-ui);
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--accent);
  line-height: 1;
}
.sw-stat-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 0.375rem;
  font-weight: 600;
}

.sw-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.875rem;
  border-radius: 999px;
  font-size: 0.8125rem;
  font-family: var(--font-ui);
  border: 1px solid var(--border);
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-weight: 500;
}
.sw-pill.active {
  border-color: #bbf7d0;
  background: var(--accent-light);
  color: var(--accent);
  font-weight: 600;
}

.sw-modal-wrap {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 2rem;
  margin: 1.5rem 0;
  box-shadow: var(--shadow-md);
}

/* ── Animations ── */
@keyframes msgIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .block-container { padding: 1.5rem 1rem 5rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# Lazy Embedding Initializer
# ==============================================================================

def _ensure_embeddings_ready() -> bool:
    """
    Lazily build product embeddings the first time semantic search is needed.
    
    Checks whether the product_embeddings table is populated. If it is empty
    and ENABLE_VECTOR_SEARCH is True, triggers a one-time build. The result
    is cached in st.session_state so the check only queries SQLite once per
    browser session.
    
    Returns:
        bool: True if embeddings are available (or were just built), False otherwise.
    """
    # Return immediately if already confirmed ready this session
    if st.session_state.get("_embeddings_ready"):
        return True
    
    # Return immediately if vector search is disabled in config
    from config import ENABLE_VECTOR_SEARCH
    if not ENABLE_VECTOR_SEARCH:
        return False
    
    import sqlite3 as _sqlite3
    import os as _os
    
    db_path = _os.path.join(_os.path.dirname(__file__), "store.db")
    
    try:
        conn = _sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM product_embeddings")
        count = cur.fetchone()[0]
        conn.close()
    except Exception:
        # Table might not exist yet — treat as empty
        count = 0
    
    if count == 0:
        # Build embeddings now, showing a one-time spinner to the user
        try:
            import vector_search
            with st.spinner("⚡ First run: building semantic search index (30–60 s)…"):
                vector_search.build_product_embeddings(verbose=False)
            st.session_state["_embeddings_ready"] = True
            return True
        except Exception as e:
            # Non-fatal: fall back gracefully; keyword search still works
            st.warning(f"Semantic search unavailable: {e}")
            return False
    else:
        st.session_state["_embeddings_ready"] = True
        return True

# ==============================================================================
# Session State Initialization
# ==============================================================================

def initialize_session_state() -> None:
    """Initialize all session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "session_token" not in st.session_state:
        st.session_state.session_token = None
    if "is_guest" not in st.session_state:
        st.session_state.is_guest = False
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "show_upgrade_banner" not in st.session_state:
        st.session_state.show_upgrade_banner = False


def display_welcome_message() -> None:
    """Display a professional welcome message for new users."""
    if not st.session_state.conversation_started and not st.session_state.messages:
        # Personalized welcome for authenticated users
        if st.session_state.authenticated and not st.session_state.is_guest:
            user_name = st.session_state.user.get('full_name', 'there')
            st.markdown(f"""
            <div class="sw-card" style="margin-bottom:1.75rem;">
              <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;">
                <div style="width:48px;height:48px;border-radius:50%;background:var(--accent);
                            display:flex;align-items:center;justify-content:center;
                            font-family:var(--font-ui);font-weight:700;font-size:1.25rem;color:#ffffff;">
                  {user_name[0].upper()}
                </div>
                <div>
                  <div style="font-family:var(--font-display);font-size:1.5rem;color:var(--text-primary);">
                    Welcome back, {user_name.split()[0]}
                  </div>
                  <div style="font-size:0.875rem;color:var(--text-secondary);">Ready to shop?</div>
                </div>
              </div>
              <div style="display:flex;gap:0.625rem;flex-wrap:wrap;margin-top:0.75rem;">
                <span class="sw-pill active">🔍 Semantic Search</span>
                <span class="sw-pill active">⭐ Rating Filters</span>
                <span class="sw-pill active">🖼️ Visual Search</span>
                <span class="sw-pill active">🛒 Instant Checkout</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="sw-card" style="margin-bottom:1.75rem;">
              <div style="font-family:var(--font-display);font-size:1.75rem;margin-bottom:0.75rem;color:var(--text-primary);">
                What are you shopping for today?
              </div>
              <div style="font-size:0.9375rem;color:var(--text-secondary);margin-bottom:1.25rem;">
                Try: <em>"organic honey under $15 with 4+ stars"</em> or upload a product photo
              </div>
              <div style="display:flex;gap:0.625rem;flex-wrap:wrap;">
                <span class="sw-pill active">🔍 Semantic Search</span>
                <span class="sw-pill active">⭐ Rating Filters</span>
                <span class="sw-pill active">🖼️ Visual Search</span>
                <span class="sw-pill active">🛒 Instant Checkout</span>
              </div>
            </div>
            """, unsafe_allow_html=True)


def render_sidebar() -> Optional[str]:
    """
    Render the sidebar with visual search functionality and user personalization.
    
    Returns:
        Optional[str]: Path to uploaded image if processed, None otherwise
    """
    with st.sidebar:
        # Personalization section for authenticated users
        if st.session_state.authenticated and not st.session_state.is_guest and ENABLE_MEMORY:
            st.markdown("### 🧠 Your Profile")
            try:
                am = AuthManager()
                
                # Get stats from AuthManager
                stats = am.get_user_stats(st.session_state.user['user_id'])
                profile = am.get_user_profile(st.session_state.user['user_id'])
                
                st.markdown(f"""
                <div class="sw-card" style="margin-bottom:1.25rem;">
                  <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.25rem;">
                    <div style="width:56px;height:56px;border-radius:50%;flex-shrink:0;
                                background:var(--accent);display:flex;align-items:center;
                                justify-content:center;font-family:var(--font-ui);
                                font-size:1.5rem;font-weight:700;color:#ffffff;">
                      {st.session_state.user['avatar_initial']}
                    </div>
                    <div style="flex:1;">
                      <div style="font-family:var(--font-display);font-size:1.125rem;color:var(--text-primary);">
                        {st.session_state.user['full_name']}
                      </div>
                      <div style="font-size:0.8125rem;color:var(--text-secondary);">
                        Member since {profile.get('created_at', '')[:10]}
                      </div>
                    </div>
                  </div>
                  <div style="display:flex;justify-content:space-around;padding-top:1rem;
                              border-top:1px solid var(--border);">
                    <div style="text-align:center;">
                      <div class="sw-stat-num">{stats.get('search_count', 0)}</div>
                      <div class="sw-stat-label">Searches</div>
                    </div>
                    <div style="text-align:center;">
                      <div class="sw-stat-num">{stats.get('order_count', 0)}</div>
                      <div class="sw-stat-label">Orders</div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Preferences will be shown here as they are learned
                # Future: Add preference learning from search/order patterns
                
            except Exception as e:
                st.caption(f"⚠️ Personalization temporarily unavailable: {str(e)}")
            
            st.markdown("---")
        
        st.markdown("### 🖼️ Visual Product Search")
        st.markdown("Upload an image to find similar products in our catalog.")
        
        st.markdown("---")
        
        uploaded_file = st.file_uploader(
            "Choose a product image",
            type=["jpg", "jpeg", "png", "webp"],
            help="Supported formats: JPG, JPEG, PNG, WEBP"
        )

        if uploaded_file:
            st.markdown("#### Preview")
            st.image(uploaded_file, use_container_width=True, caption=uploaded_file.name)
            
            st.markdown("---")

            if st.button("🔍 Find Similar Products", use_container_width=True, type="primary"):
                suffix = os.path.splitext(uploaded_file.name)[1] or ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    image_path = tmp.name

                prompt = f"I uploaded a product image. Please analyze it and find similar products in the store. Image path: {image_path}"
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.pending_image = uploaded_file.name
                st.session_state.conversation_started = True
                
                # Log search in memory manager
                if ENABLE_MEMORY and st.session_state.authenticated and not st.session_state.is_guest:
                    try:
                        mm = MemoryManager()
                        mm.log_search(st.session_state.user['user_id'], f"Visual search: {uploaded_file.name}")
                    except Exception:
                        pass
                
                st.rerun()
        
        st.markdown("---")
        
        # Additional sidebar information
        with st.expander("ℹ️ How It Works"):
            st.markdown("""
            **Visual Search Process:**
            1. Upload a product image
            2. AI analyzes the image attributes
            3. Matches similar products in our database
            4. Displays results with ratings and prices
            
            **Supported Products:**
            - Organic & natural foods
            - Oils & condiments
            - Nuts, seeds & grains
            - Beverages & snacks
            """)
        
        # Statistics or additional info
        with st.expander("📊 Platform Stats"):
            st.markdown("""
            - 🏪 **32** Premium Products
            - ⭐ **4.3** Average Rating
            - 🌱 **40%** Organic Options
            - 🚚 **3-5** Days Delivery
            """)


def render_chat_message(msg: dict) -> None:
    """
    Render a single chat message with proper formatting.
    
    Args:
        msg: Message dictionary with 'role' and 'content' keys
    """
    with st.chat_message(msg["role"]):
        if msg["role"] == "user" and msg["content"].startswith("I uploaded a product image"):
            filename = msg["content"].split("Image path:")[-1].strip()
            st.markdown(f"🖼️ **Visual Search:** `{os.path.basename(filename)}`")
        else:
            st.markdown(msg["content"].replace("$", r"\$"))


def render_user_header() -> None:
    """Render authenticated user header with profile dropdown."""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;">
          <span style="font-size:1.75rem;">🛍️</span>
          <span style="font-family:var(--font-display);font-size:1.5rem;color:var(--text-primary);
                       letter-spacing:-0.02em;font-weight:600;">ShopWise AI</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <p style="font-family:var(--font-ui);font-size:0.875rem;color:var(--text-secondary);
                  margin-top:1rem;text-align:center;letter-spacing:0.02em;font-weight:400;">
          Intelligent Shopping Companion
        </p>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.session_state.authenticated:
            user = st.session_state.user
            username = user.get('username', 'User')
            avatar = user.get('avatar_initial', 'U')
            
            # User dropdown using popover
            with st.popover(f"👤 {username} ▾"):
                st.markdown(f"""
                <div style="text-align:center;padding:0.75rem 0 1.25rem;">
                  <div style="width:64px;height:64px;border-radius:50%;
                              background:var(--accent);display:flex;align-items:center;
                              justify-content:center;margin:0 auto 1rem;
                              font-family:var(--font-ui);font-size:1.75rem;font-weight:700;color:#ffffff;">
                    {avatar}
                  </div>
                  <div style="font-family:var(--font-display);font-size:1.125rem;color:var(--text-primary);font-weight:600;">
                    {user.get('full_name', username)}
                  </div>
                  <div style="font-family:var(--font-ui);font-size:0.875rem;color:var(--text-secondary);margin-top:0.375rem;">
                    {user.get('email', '')}
                  </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # My Orders button
                if st.button("📦 My Orders", use_container_width=True):
                    st.session_state.show_orders = True
                
                # Profile button
                if st.button("⚙️ Profile Settings", use_container_width=True):
                    st.session_state.show_profile = True
                
                # Change Password (only for non-guest)
                if not st.session_state.is_guest:
                    if st.button("🔑 Change Password", use_container_width=True):
                        st.session_state.show_password = True
                
                st.markdown("---")
                
                # Sign out button
                if st.button("🚪 Sign Out", use_container_width=True, type="primary"):
                    if not st.session_state.is_guest:
                        am = AuthManager()
                        am.logout(st.session_state.session_token)
                    
                    # Clear session
                    st.session_state.authenticated = False
                    st.session_state.user = None
                    st.session_state.session_token = None
                    st.session_state.is_guest = False
                    st.session_state.messages = []
                    st.session_state.conversation_started = False
                    st.rerun()


def render_guest_upgrade_banner() -> None:
    """Render guest-to-user upgrade banner."""
    if st.session_state.is_guest and st.session_state.show_upgrade_banner:
        st.markdown("""
        <div style="background:var(--bg-surface);border:1px solid var(--warning);
                    border-radius:var(--r-md);padding:1rem 1.25rem;margin-bottom:1.25rem;box-shadow:var(--shadow-sm);">
          <span style="color:var(--warning);font-weight:600;">💡 Create a free account</span>
          <span style="color:var(--text-secondary);font-size:0.9375rem;">
            &nbsp;to save your preferences and order history
          </span>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Create Account", use_container_width=True, type="primary"):
                st.session_state.authenticated = False
                st.session_state.is_guest = False
                st.rerun()
        with col2:
            if st.button("Maybe Later", use_container_width=True):
                st.session_state.show_upgrade_banner = False
                st.rerun()


def process_agent_response(messages: list) -> str:
    """
    Process messages through the shopping agent.
    
    Args:
        messages: List of conversation messages
        
    Returns:
        str: Agent response content
    """
    # Set user_id for checkout functionality
    user_id = "guest"
    if st.session_state.authenticated:
        user_id = st.session_state.user.get('user_id', 'guest')
    
    set_user_context(user_id)
    
    # Invoke agent
    result = agent.invoke(
        {"messages": messages},
        config={"configurable": {"thread_id": st.session_state.thread_id}}
    )
    response = result["messages"][-1].content.replace("`", "")
    return response


# ==============================================================================
# Main Application
# ==============================================================================

def main() -> None:
    """Main application entry point."""
    
    # Initialize session state
    initialize_session_state()
    
    # ==========================================================================
    # Authentication Flow
    # ==========================================================================
    if ENABLE_AUTH:
        # Check if we have an existing session
        if st.session_state.session_token and not st.session_state.authenticated:
            am = AuthManager()
            user = am.verify_session(st.session_state.session_token)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.is_guest = False
                st.session_state.thread_id = f"thread_{user['user_id']}"
        
        # If not authenticated and not guest, show auth page
        if not st.session_state.authenticated:
            result = render_auth_page()
            
            if result:
                if result.get('is_guest'):
                    # Guest login
                    st.session_state.authenticated = True
                    st.session_state.user = result
                    st.session_state.is_guest = True
                    st.session_state.thread_id = f"thread_{result['user_id']}"
                else:
                    # Regular login
                    st.session_state.authenticated = True
                    st.session_state.user = result
                    st.session_state.session_token = result['session_token']
                    st.session_state.is_guest = False
                    st.session_state.thread_id = f"thread_{result['user_id']}"
                
                st.rerun()
            else:
                return  # Stay on auth page
    else:
        # Auth disabled - set default guest user
        if not st.session_state.authenticated:
            st.session_state.authenticated = True
            st.session_state.is_guest = True
            st.session_state.user = {
                "user_id": "guest",
                "username": "Guest",
                "full_name": "Guest User",
                "avatar_initial": "G"
            }
    
    # ==========================================================================
    # Main Application UI
    # ==========================================================================
    
    # Render user header
    render_user_header()
    
    # Check for search/order count to show upgrade banner
    if st.session_state.is_guest and len(st.session_state.messages) >= 6:
        st.session_state.show_upgrade_banner = True
    
    # Render upgrade banner for guests
    render_guest_upgrade_banner()
    
    # Display welcome message
    display_welcome_message()
    
    # Render sidebar and get image upload status
    render_sidebar()
    
    # Handle modal dialogs using expanders
    if st.session_state.get('show_orders', False):
        st.markdown("---")
        st.markdown('<div class="sw-modal-wrap">', unsafe_allow_html=True)
        st.markdown("### 📦 Your Orders")
        render_orders_modal(st.session_state.user)
        if st.button("✖ Close Orders", use_container_width=True, key="close_orders"):
            st.session_state.show_orders = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")
        # Stop rendering the rest when modal is open
        return
    
    if st.session_state.get('show_profile', False):
        st.markdown("---")
        st.markdown('<div class="sw-modal-wrap">', unsafe_allow_html=True)
        st.markdown("### ⚙️ Profile Settings")
        render_profile_modal(st.session_state.user)
        if st.button("✖ Close Profile", use_container_width=True, key="close_profile"):
            st.session_state.show_profile = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")
        # Stop rendering the rest when modal is open
        return
    
    if st.session_state.get('show_password', False):
        st.markdown("---")
        st.markdown('<div class="sw-modal-wrap">', unsafe_allow_html=True)
        st.markdown("### 🔑 Change Password")
        render_password_modal(st.session_state.user)
        if st.button("✖ Close Password", use_container_width=True, key="close_password"):
            st.session_state.show_password = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")
        # Stop rendering the rest when modal is open
        return
    
    # Render conversation history
    for msg in st.session_state.messages:
        render_chat_message(msg)
    
    # Process pending image search
    if (
        st.session_state.messages
        and st.session_state.messages[-1]["role"] == "user"
        and "pending_image" in st.session_state
    ):
        with st.chat_message("assistant"):
            with st.spinner("🔍 Analyzing image and searching our catalog..."):
                response = process_agent_response(st.session_state.messages)
            st.markdown(response.replace("$", r"\$"))

        st.session_state.messages.append({"role": "assistant", "content": response})
        del st.session_state.pending_image
        st.rerun()
    
    # Ensure embeddings exist before any semantic search might be triggered
    _ensure_embeddings_ready()
    
    # Chat input
    if prompt := st.chat_input(
        "💬 Describe what you're looking for (e.g., 'organic honey under $15 with 4+ stars')",
        key="chat_input"
    ):
        st.session_state.conversation_started = True
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Log search in memory manager
        if ENABLE_MEMORY and st.session_state.authenticated and not st.session_state.is_guest:
            try:
                mm = MemoryManager()
                mm.log_search(
                    user_id=st.session_state.user['user_id'],
                    query=prompt,
                    filters={},  # No filters at input time
                    result_ids=[],  # Will be updated after search results
                    ordered_product_id=None
                )
            except Exception:
                pass
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤔 Searching and analyzing products..."):
                response = process_agent_response(st.session_state.messages)
            st.markdown(response.replace("$", r"\$"))

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()


if __name__ == "__main__":
    main()
