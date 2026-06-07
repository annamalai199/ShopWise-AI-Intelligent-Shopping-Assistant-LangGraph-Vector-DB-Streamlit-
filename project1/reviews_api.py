"""
ShopWise AI - Product Reviews API Module

Provides a robust API for retrieving and aggregating product review data
from the SQLite database. Supports both single and batch product rating queries.

This module acts as the data access layer for product ratings and reviews,
abstracting database operations and providing clean interfaces for the agent.

Features:
    - Single product rating retrieval
    - Batch product rating queries (optimized with single SQL query)
    - Aggregated statistics (average rating, review count)
    - Error handling for missing products

Author: ShopWise Engineering Team
License: MIT
"""

import sqlite3
import os
from typing import Dict, List, Optional

# ==============================================================================
# Configuration
# ==============================================================================

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")


# ==============================================================================
# Database Connection Utility
# ==============================================================================

def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a database connection with optimized settings.
    
    Returns:
        sqlite3.Connection: Database connection with row factory enabled
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==============================================================================
# Public API Functions
# ==============================================================================

def get_product_rating(product_id: int) -> Dict[str, any]:
    """
    Retrieve average rating and review count for a single product.
    
    Args:
        product_id (int): Unique identifier of the product
        
    Returns:
        dict: Dictionary containing:
            - product_id (int): The product identifier
            - average_rating (float): Average rating rounded to 2 decimal places
            - review_count (int): Total number of reviews
            
    Example:
        >>> get_product_rating(1)
        {'product_id': 1, 'average_rating': 4.63, 'review_count': 4}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT AVG(rating) as avg_rating, COUNT(*) as review_count 
        FROM reviews 
        WHERE product_id = ?
        """,
        (product_id,),
    )
    row = cursor.fetchone()
    conn.close()

    avg = round(row["avg_rating"], 2) if row and row["avg_rating"] is not None else 0.0
    count = row["review_count"] if row else 0
    
    return {
        "product_id": product_id,
        "average_rating": avg,
        "review_count": count
    }


def get_ratings_for_products(product_ids: List[int]) -> List[Dict[str, any]]:
    """
    Retrieve ratings for multiple products in a single optimized query.
    
    This function is more efficient than calling get_product_rating() multiple
    times, as it retrieves all ratings in a single database query.
    
    Args:
        product_ids (List[int]): List of product identifiers to query
        
    Returns:
        List[dict]: List of dictionaries, one per product, each containing:
            - product_id (int): The product identifier
            - average_rating (float): Average rating rounded to 2 decimal places
            - review_count (int): Total number of reviews
            
    Example:
        >>> get_ratings_for_products([1, 3, 5])
        [
            {'product_id': 1, 'average_rating': 4.63, 'review_count': 4},
            {'product_id': 3, 'average_rating': 4.83, 'review_count': 3},
            {'product_id': 5, 'average_rating': 4.63, 'review_count': 4}
        ]
    """
    if not product_ids:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholders = ",".join("?" * len(product_ids))
    cursor.execute(
        f"""
        SELECT 
            product_id,
            AVG(rating) as avg_rating,
            COUNT(*) as review_count
        FROM reviews
        WHERE product_id IN ({placeholders})
        GROUP BY product_id
        """,
        product_ids,
    )
    rows = cursor.fetchall()
    conn.close()

    # Create a mapping of product_id to ratings
    ratings_map = {
        row["product_id"]: {
            "average_rating": round(row["avg_rating"], 2),
            "review_count": row["review_count"]
        }
        for row in rows
    }
    
    # Return results in the same order as input, with defaults for missing products
    return [
        {
            "product_id": pid,
            "average_rating": ratings_map.get(pid, {}).get("average_rating", 0.0),
            "review_count": ratings_map.get(pid, {}).get("review_count", 0),
        }
        for pid in product_ids
    ]


def get_top_rated_products(min_rating: float = 4.0, limit: int = 10) -> List[Dict[str, any]]:
    """
    Retrieve top-rated products based on average rating.
    
    Args:
        min_rating (float): Minimum average rating threshold (default: 4.0)
        limit (int): Maximum number of products to return (default: 10)
        
    Returns:
        List[dict]: List of top-rated products with rating information
        
    Example:
        >>> get_top_rated_products(min_rating=4.5, limit=5)
        [
            {'product_id': 3, 'average_rating': 4.83, 'review_count': 3},
            {'product_id': 7, 'average_rating': 4.75, 'review_count': 4},
            ...
        ]
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT 
            product_id,
            AVG(rating) as avg_rating,
            COUNT(*) as review_count
        FROM reviews
        GROUP BY product_id
        HAVING AVG(rating) >= ?
        ORDER BY avg_rating DESC, review_count DESC
        LIMIT ?
        """,
        (min_rating, limit),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "product_id": row["product_id"],
            "average_rating": round(row["avg_rating"], 2),
            "review_count": row["review_count"]
        }
        for row in rows
    ]


# ==============================================================================
# CLI Testing Interface
# ==============================================================================

if __name__ == "__main__":
    """
    Command-line interface for testing the reviews API.
    Demonstrates both single and batch rating queries.
    """
    print("=" * 70)
    print("ShopWise AI - Reviews API Testing Interface")
    print("=" * 70)
    print()
    
    # Test 1: Single product rating
    print("TEST 1: Single Product Rating")
    print("-" * 70)
    result = get_product_rating(1)
    print(f"Product {result['product_id']}:")
    print(f"  ⭐ Average Rating: {result['average_rating']}/5.0")
    print(f"  📝 Total Reviews: {result['review_count']}")
    print()

    # Test 2: Batch ratings
    print("TEST 2: Batch Product Ratings")
    print("-" * 70)
    test_ids = [1, 3, 5, 7, 9]
    results = get_ratings_for_products(test_ids)
    for r in results:
        print(f"Product {r['product_id']}: "
              f"⭐ {r['average_rating']}/5.0 "
              f"({r['review_count']} reviews)")
    print()
    
    # Test 3: Top rated products
    print("TEST 3: Top Rated Products (4.5+ stars)")
    print("-" * 70)
    top_products = get_top_rated_products(min_rating=4.5, limit=5)
    for i, p in enumerate(top_products, 1):
        print(f"#{i}. Product {p['product_id']}: "
              f"⭐ {p['average_rating']}/5.0 "
              f"({p['review_count']} reviews)")
    
    print("\n" + "=" * 70)
