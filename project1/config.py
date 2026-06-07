"""
ShopWise AI - Configuration Module

Central configuration for feature flags and system settings.
Allows enabling/disabling features for graceful degradation.

Author: ShopWise Engineering Team
License: MIT
"""

# ==============================================================================
# Feature Flags
# ==============================================================================

# Authentication
ENABLE_AUTH = True
"""Enable user authentication and registration system"""

# Memory and Personalization
ENABLE_MEMORY = True
"""Enable persistent user memory and personalization features"""

# Vector Search
ENABLE_VECTOR_SEARCH = True
"""Enable semantic product search using sentence transformers"""

# LangGraph Checkpointing
ENABLE_CHECKPOINTING = True
"""Enable stateful conversation memory across sessions"""


# ==============================================================================
# System Configuration
# ==============================================================================

# Database
DB_PATH = "store.db"
"""Path to SQLite database file"""

# Memory Manager
MEMORY_MIN_CONFIDENCE = 0.3
"""Minimum confidence threshold for preferences"""

MEMORY_CONFIDENCE_DECAY = 0.9
"""Confidence decay factor for non-matching preferences"""

MEMORY_CONFIDENCE_BOOST = 0.2
"""Confidence boost for matching preferences"""

# Vector Search
VECTOR_MODEL_NAME = "all-MiniLM-L6-v2"
"""Sentence transformer model for embeddings"""

VECTOR_SIMILARITY_THRESHOLD = 0.3
"""Minimum cosine similarity for semantic matches"""

VECTOR_TOP_K = 5
"""Default number of results for semantic search"""

# LangGraph
LANGGRAPH_VERBOSE = False
"""Enable verbose logging for LangGraph agent"""

# UI
SHOW_PERSONALIZATION_BANNER = True
"""Show personalization banner in UI"""

SHOW_SEMANTIC_BADGES = True
"""Show semantic match badges in search results"""


# ==============================================================================
# Helper Functions
# ==============================================================================

def is_feature_enabled(feature_name: str) -> bool:
    """
    Check if a feature is enabled.
    
    Args:
        feature_name (str): Name of the feature
        
    Returns:
        bool: True if enabled, False otherwise
    """
    features = {
        'auth': ENABLE_AUTH,
        'memory': ENABLE_MEMORY,
        'vector_search': ENABLE_VECTOR_SEARCH,
        'checkpointing': ENABLE_CHECKPOINTING
    }
    return features.get(feature_name.lower(), False)


def get_config_summary() -> str:
    """
    Get a formatted summary of current configuration.
    
    Returns:
        str: Configuration summary
    """
    lines = [
        "ShopWise AI - Configuration Summary",
        "=" * 50,
        "",
        "Feature Flags:",
        f"  • Authentication: {'✅ Enabled' if ENABLE_AUTH else '❌ Disabled'}",
        f"  • Memory & Personalization: {'✅ Enabled' if ENABLE_MEMORY else '❌ Disabled'}",
        f"  • Vector Search: {'✅ Enabled' if ENABLE_VECTOR_SEARCH else '❌ Disabled'}",
        f"  • Checkpointing: {'✅ Enabled' if ENABLE_CHECKPOINTING else '❌ Disabled'}",
        "",
        "System Settings:",
        f"  • Database: {DB_PATH}",
        f"  • Vector Model: {VECTOR_MODEL_NAME}",
        f"  • Similarity Threshold: {VECTOR_SIMILARITY_THRESHOLD}",
        ""
    ]
    return "\n".join(lines)


# ==============================================================================
# CLI Interface
# ==============================================================================

if __name__ == "__main__":
    print(get_config_summary())
