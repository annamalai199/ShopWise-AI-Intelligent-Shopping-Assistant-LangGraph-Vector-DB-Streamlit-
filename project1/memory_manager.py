"""
ShopWise AI - Memory Manager Module

Implements persistent user memory and personalization using SQLite.
Tracks user preferences, search history, and generates personalized recommendations.

Author: ShopWise Engineering Team
License: MIT
"""

import json
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import os

# ==============================================================================
# Configuration
# ==============================================================================

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")

# Preference types
PREF_LIKED_CATEGORY = "liked_category"
PREF_PRICE_RANGE = "price_range"
PREF_ORGANIC_PREFERENCE = "organic_preference"
PREF_MIN_RATING = "min_rating"

# Confidence thresholds
MIN_CONFIDENCE_THRESHOLD = 0.3
CONFIDENCE_DECAY = 0.9
CONFIDENCE_BOOST = 0.2


# ==============================================================================
# Memory Manager Class
# ==============================================================================

class MemoryManager:
    """
    Manages user memory, preferences, and search history for personalization.
    
    This class provides methods to track user behavior, infer preferences,
    and generate personalized recommendations based on historical data.
    """
    
    def __init__(self, db_path: str = DB_PATH):
        """
        Initialize the memory manager.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Create and return a database connection.
        
        Returns:
            sqlite3.Connection: Database connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_or_create_user(self, user_id: str, display_name: str = "Guest") -> Dict[str, Any]:
        """
        Get existing user profile or create a new one.
        
        Args:
            user_id (str): Unique user identifier (UUID)
            display_name (str): Display name for the user
            
        Returns:
            dict: User profile with user_id, display_name, created_at, last_seen
            
        Example:
            >>> mm = MemoryManager()
            >>> user = mm.get_or_create_user("abc-123", "John")
            >>> print(user['user_id'])
            'abc-123'
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Try to get existing user
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            if user:
                # Update last_seen
                cursor.execute(
                    "UPDATE user_profiles SET last_seen = datetime('now') WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                return dict(user)
            else:
                # Create new user
                cursor.execute(
                    "INSERT INTO user_profiles (user_id, display_name, last_seen) VALUES (?, ?, datetime('now'))",
                    (user_id, display_name)
                )
                conn.commit()
                
                cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
                user = cursor.fetchone()
                return dict(user)
        finally:
            conn.close()
    
    def log_search(
        self,
        user_id: str,
        query: str,
        filters: Dict[str, Any],
        result_ids: List[int],
        ordered_product_id: Optional[int] = None
    ) -> int:
        """
        Log a user search to history.
        
        Args:
            user_id (str): User identifier
            query (str): Search query text
            filters (dict): Search filters (max_price, is_organic, min_rating)
            result_ids (list): List of product IDs returned in search results
            ordered_product_id (int, optional): Product ID if user ordered
            
        Returns:
            int: ID of the created search history record
            
        Example:
            >>> mm.log_search("user123", "organic honey", {"max_price": 20}, [1, 3, 5])
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO search_history 
                (user_id, query, filters, result_ids, ordered_product_id)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    user_id,
                    query,
                    json.dumps(filters),
                    json.dumps(result_ids),
                    ordered_product_id
                )
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def log_order(self, user_id: str, product_id: int, search_id: Optional[int] = None) -> None:
        """
        Log a product order and update search history.
        
        Args:
            user_id (str): User identifier
            product_id (int): Ordered product ID
            search_id (int, optional): Associated search history ID
            
        Example:
            >>> mm.log_order("user123", 5)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Update most recent search with ordered product
            if search_id:
                cursor.execute(
                    "UPDATE search_history SET ordered_product_id = ? WHERE id = ?",
                    (product_id, search_id)
                )
            else:
                cursor.execute(
                    """UPDATE search_history 
                    SET ordered_product_id = ? 
                    WHERE user_id = ? AND ordered_product_id IS NULL
                    ORDER BY searched_at DESC LIMIT 1""",
                    (product_id, user_id)
                )
            conn.commit()
        finally:
            conn.close()
    
    def get_user_context(self, user_id: str) -> str:
        """
        Generate formatted user context string for agent prompt injection.
        
        Args:
            user_id (str): User identifier
            
        Returns:
            str: Formatted context string with user history and preferences
            
        Example:
            >>> context = mm.get_user_context("user123")
            >>> print(context)
            USER CONTEXT:
            Recent searches: organic honey, coffee beans
            Favorite categories: honey, coffee
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            context_parts = ["USER PERSONALIZATION CONTEXT:"]
            
            # Get last 3 searches
            cursor.execute(
                """SELECT query, filters, ordered_product_id 
                FROM search_history 
                WHERE user_id = ? 
                ORDER BY searched_at DESC LIMIT 3""",
                (user_id,)
            )
            searches = cursor.fetchall()
            
            if searches:
                search_list = []
                for s in searches:
                    search_text = f"'{s['query']}'"
                    if s['ordered_product_id']:
                        search_text += " (ordered)"
                    search_list.append(search_text)
                context_parts.append(f"• Recent searches: {', '.join(search_list)}")
            
            # Get most ordered categories
            cursor.execute(
                """SELECT p.category, COUNT(*) as count
                FROM search_history sh
                JOIN products p ON p.id = sh.ordered_product_id
                WHERE sh.user_id = ? AND sh.ordered_product_id IS NOT NULL
                GROUP BY p.category
                ORDER BY count DESC LIMIT 3""",
                (user_id,)
            )
            categories = cursor.fetchall()
            
            if categories:
                cat_list = [f"{c['category']} ({c['count']}x)" for c in categories]
                context_parts.append(f"• Favorite categories: {', '.join(cat_list)}")
            
            # Get preferences
            cursor.execute(
                """SELECT preference_type, preference_value, confidence
                FROM user_preferences
                WHERE user_id = ? AND confidence > ?
                ORDER BY confidence DESC""",
                (user_id, MIN_CONFIDENCE_THRESHOLD)
            )
            prefs = cursor.fetchall()
            
            if prefs:
                pref_lines = []
                for p in prefs:
                    pref_type = p['preference_type'].replace('_', ' ').title()
                    pref_lines.append(f"  - {pref_type}: {p['preference_value']} (confidence: {p['confidence']:.2f})")
                context_parts.append("• Inferred preferences:")
                context_parts.extend(pref_lines)
            
            # Get average price of ordered items
            cursor.execute(
                """SELECT AVG(p.price) as avg_price
                FROM search_history sh
                JOIN products p ON p.id = sh.ordered_product_id
                WHERE sh.user_id = ? AND sh.ordered_product_id IS NOT NULL""",
                (user_id,)
            )
            avg_price = cursor.fetchone()
            if avg_price and avg_price['avg_price']:
                context_parts.append(f"• Average order price: ${avg_price['avg_price']:.2f}")
            
            if len(context_parts) == 1:
                return ""  # No context available
            
            return "\n".join(context_parts)
            
        finally:
            conn.close()

    
    def get_personalized_suggestions(self, user_id: str, limit: int = 5) -> List[int]:
        """
        Get personalized product suggestions based on user history.
        
        Args:
            user_id (str): User identifier
            limit (int): Maximum number of suggestions to return
            
        Returns:
            list: List of product IDs recommended for the user
            
        Example:
            >>> suggestions = mm.get_personalized_suggestions("user123", 3)
            >>> print(suggestions)
            [1, 5, 7]
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get user's favorite categories
            cursor.execute(
                """SELECT p.category, COUNT(*) as count
                FROM search_history sh
                JOIN products p ON p.id = sh.ordered_product_id
                WHERE sh.user_id = ? AND sh.ordered_product_id IS NOT NULL
                GROUP BY p.category
                ORDER BY count DESC LIMIT 3""",
                (user_id,)
            )
            categories = [row['category'] for row in cursor.fetchall()]
            
            if not categories:
                # No order history, return top-rated products
                cursor.execute(
                    """SELECT p.id, AVG(r.rating) as avg_rating
                    FROM products p
                    JOIN reviews r ON r.product_id = p.id
                    GROUP BY p.id
                    ORDER BY avg_rating DESC
                    LIMIT ?""",
                    (limit,)
                )
                return [row['id'] for row in cursor.fetchall()]
            
            # Get products from favorite categories
            placeholders = ','.join('?' * len(categories))
            cursor.execute(
                f"""SELECT p.id, AVG(r.rating) as avg_rating
                FROM products p
                JOIN reviews r ON r.product_id = p.id
                WHERE p.category IN ({placeholders})
                AND p.id NOT IN (
                    SELECT ordered_product_id FROM search_history 
                    WHERE user_id = ? AND ordered_product_id IS NOT NULL
                )
                GROUP BY p.id
                ORDER BY avg_rating DESC
                LIMIT ?""",
                (*categories, user_id, limit)
            )
            
            return [row['id'] for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    def update_preferences(
        self,
        user_id: str,
        search_filters: Dict[str, Any],
        ordered_product: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Auto-infer and update user preferences from behavior.
        
        Args:
            user_id (str): User identifier
            search_filters (dict): Filters used in search
            ordered_product (dict, optional): Product that was ordered
            
        Example:
            >>> mm.update_preferences("user123", {"max_price": 20, "is_organic": True})
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Update price range preference
            if 'max_price' in search_filters and search_filters['max_price']:
                self._update_preference(
                    cursor,
                    user_id,
                    PREF_PRICE_RANGE,
                    f"${search_filters['max_price']:.2f}",
                    CONFIDENCE_BOOST
                )
            
            # Update organic preference
            if 'is_organic' in search_filters and search_filters['is_organic'] is not None:
                organic_pref = "Prefers organic" if search_filters['is_organic'] else "No preference"
                self._update_preference(
                    cursor,
                    user_id,
                    PREF_ORGANIC_PREFERENCE,
                    organic_pref,
                    CONFIDENCE_BOOST
                )
            
            # Update min rating preference
            if 'min_rating' in search_filters and search_filters['min_rating']:
                self._update_preference(
                    cursor,
                    user_id,
                    PREF_MIN_RATING,
                    f"{search_filters['min_rating']}+ stars",
                    CONFIDENCE_BOOST
                )
            
            # Update category preference if product ordered
            if ordered_product:
                self._update_preference(
                    cursor,
                    user_id,
                    PREF_LIKED_CATEGORY,
                    ordered_product.get('category', 'unknown'),
                    CONFIDENCE_BOOST * 2  # Stronger signal
                )
            
            conn.commit()
            
        finally:
            conn.close()
    
    def _update_preference(
        self,
        cursor: sqlite3.Cursor,
        user_id: str,
        pref_type: str,
        pref_value: str,
        confidence_change: float
    ) -> None:
        """
        Internal method to update a single preference.
        
        Args:
            cursor: Database cursor
            user_id: User identifier
            pref_type: Type of preference
            pref_value: Preference value
            confidence_change: Amount to adjust confidence
        """
        # Check if preference exists
        cursor.execute(
            """SELECT id, confidence FROM user_preferences
            WHERE user_id = ? AND preference_type = ? AND preference_value = ?""",
            (user_id, pref_type, pref_value)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Boost confidence
            new_confidence = min(1.0, existing['confidence'] + confidence_change)
            cursor.execute(
                """UPDATE user_preferences 
                SET confidence = ?, updated_at = datetime('now')
                WHERE id = ?""",
                (new_confidence, existing['id'])
            )
        else:
            # Create new preference
            cursor.execute(
                """INSERT INTO user_preferences 
                (user_id, preference_type, preference_value, confidence)
                VALUES (?, ?, ?, ?)""",
                (user_id, pref_type, pref_value, confidence_change)
            )
        
        # Decay confidence of other preferences of same type
        cursor.execute(
            """UPDATE user_preferences 
            SET confidence = confidence * ?
            WHERE user_id = ? AND preference_type = ? AND preference_value != ?""",
            (CONFIDENCE_DECAY, user_id, pref_type, pref_value)
        )
    
    def get_recent_search_summary(self, user_id: str) -> Optional[str]:
        """
        Get a summary of the user's most recent search.
        
        Args:
            user_id (str): User identifier
            
        Returns:
            str: Summary text or None if no searches
            
        Example:
            >>> summary = mm.get_recent_search_summary("user123")
            >>> print(summary)
            'organic honey under $20'
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT query, filters FROM search_history
                WHERE user_id = ?
                ORDER BY searched_at DESC LIMIT 1""",
                (user_id,)
            )
            search = cursor.fetchone()
            
            if not search:
                return None
            
            return search['query']
            
        finally:
            conn.close()
    
    def reset_user_data(self, user_id: str) -> None:
        """
        Delete all data for a specific user.
        
        Args:
            user_id (str): User identifier to reset
            
        Example:
            >>> mm.reset_user_data("user123")
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM search_history WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM user_preferences WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
            conn.commit()
        finally:
            conn.close()


# ==============================================================================
# Module-level functions
# ==============================================================================

def get_memory_manager() -> MemoryManager:
    """
    Get a MemoryManager instance.
    
    Returns:
        MemoryManager: Initialized memory manager
    """
    return MemoryManager()


# ==============================================================================
# CLI Testing Interface
# ==============================================================================

if __name__ == "__main__":
    """Test the memory manager functionality."""
    print("=" * 70)
    print("ShopWise AI - Memory Manager Testing")
    print("=" * 70)
    print()
    
    mm = MemoryManager()
    test_user_id = "test_user_123"
    
    # Test 1: Create user
    print("TEST 1: Create/Get User")
    print("-" * 70)
    user = mm.get_or_create_user(test_user_id, "Test User")
    print(f"User created: {user['user_id']}")
    print(f"Display name: {user['display_name']}")
    print()
    
    # Test 2: Log searches
    print("TEST 2: Log Search History")
    print("-" * 70)
    mm.log_search(test_user_id, "organic honey", {"max_price": 20, "is_organic": True}, [1, 3, 5])
    mm.log_search(test_user_id, "coffee", {"max_price": 15}, [23])
    print("✓ Logged 2 searches")
    print()
    
    # Test 3: Update preferences
    print("TEST 3: Update Preferences")
    print("-" * 70)
    mm.update_preferences(test_user_id, {"max_price": 20, "is_organic": True})
    print("✓ Preferences updated")
    print()
    
    # Test 4: Get context
    print("TEST 4: Get User Context")
    print("-" * 70)
    context = mm.get_user_context(test_user_id)
    print(context if context else "(No context available)")
    print()
    
    # Test 5: Get suggestions
    print("TEST 5: Get Personalized Suggestions")
    print("-" * 70)
    suggestions = mm.get_personalized_suggestions(test_user_id, 3)
    print(f"Suggested product IDs: {suggestions}")
    print()
    
    print("=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
