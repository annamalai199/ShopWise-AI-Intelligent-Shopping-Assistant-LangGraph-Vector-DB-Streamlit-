"""
ShopWise AI - Vector Search Module

Implements semantic product search using sentence transformers and SQLite.
Enables natural language queries like "something for breakfast" to find relevant products.

Author: ShopWise Engineering Team
License: MIT
"""

import sqlite3
import numpy as np
import os
from typing import List, Tuple, Optional
import json

# Lazy import to avoid loading model until needed
_model = None

# ==============================================================================
# Configuration
# ==============================================================================

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")
MODEL_NAME = "all-MiniLM-L6-v2"  # 80MB, fast, good quality
EMBEDDING_DIM = 384  # Dimension of all-MiniLM-L6-v2 embeddings


# ==============================================================================
# Model Loading
# ==============================================================================

def get_model():
    """
    Lazy load the sentence transformer model with Streamlit caching.
    
    Returns:
        SentenceTransformer: Loaded model instance
    """
    global _model
    if _model is None:
        try:
            # Try to use Streamlit caching if available
            try:
                import streamlit as st
                @st.cache_resource
                def _load_model():
                    from sentence_transformers import SentenceTransformer
                    return SentenceTransformer(MODEL_NAME)
                _model = _load_model()
                print(f"✓ Loaded embedding model with Streamlit caching: {MODEL_NAME}")
            except ImportError:
                # Fallback to regular loading if Streamlit not available
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer(MODEL_NAME)
                print(f"✓ Loaded embedding model: {MODEL_NAME}")
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
    return _model


# ==============================================================================
# Database Operations
# ==============================================================================

def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a database connection.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==============================================================================
# Embedding Generation
# ==============================================================================

def build_product_embeddings(verbose: bool = True) -> int:
    """
    Generate and store embeddings for all products in the database.
    
    This should be run once during setup or when products are updated.
    Creates embeddings from product name, description, and category.
    
    Args:
        verbose (bool): Whether to print progress messages
        
    Returns:
        int: Number of products embedded
        
    Example:
        >>> count = build_product_embeddings()
        >>> print(f"Embedded {count} products")
    """
    model = get_model()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all products
        cursor.execute(
            "SELECT id, name, description, category FROM products ORDER BY id"
        )
        products = cursor.fetchall()
        
        if verbose:
            print(f"🔄 Generating embeddings for {len(products)} products...")
        
        embedded_count = 0
        
        for product in products:
            # Create rich text representation
            text = f"{product['name']}. {product['description']}. Category: {product['category']}"
            
            # Generate embedding
            embedding = model.encode(text, convert_to_numpy=True)
            
            # Convert numpy array to bytes for storage
            embedding_bytes = embedding.tobytes()
            
            # Store in database
            cursor.execute(
                """INSERT OR REPLACE INTO product_embeddings 
                (product_id, embedding, model_version) VALUES (?, ?, ?)""",
                (product['id'], embedding_bytes, MODEL_NAME)
            )
            
            embedded_count += 1
            
            if verbose and embedded_count % 10 == 0:
                print(f"   Embedded {embedded_count}/{len(products)} products...")
        
        conn.commit()
        
        if verbose:
            print(f"✅ Successfully embedded {embedded_count} products")
        
        return embedded_count
        
    except Exception as e:
        conn.rollback()
        if verbose:
            print(f"❌ Error building embeddings: {e}")
        raise
    finally:
        conn.close()


# ==============================================================================
# Semantic Search
# ==============================================================================

def semantic_search(
    query: str,
    top_k: int = 5,
    threshold: float = 0.3,
    filters: Optional[dict] = None
) -> List[Tuple[int, float]]:
    """
    Find products semantically similar to the query using vector search.
    
    This enables natural language queries like:
    - "something to put on toast" → finds honey, jam, spreads
    - "healthy breakfast" → finds oats, granola, organic products
    - "gift for a foodie" → finds premium specialty items
    
    Args:
        query (str): Natural language search query
        top_k (int): Maximum number of results to return (default: 5)
        threshold (float): Minimum similarity score (0-1, default: 0.3)
        filters (dict, optional): Additional filters (max_price, is_organic)
        
    Returns:
        list: List of (product_id, similarity_score) tuples, sorted by score descending
        
    Example:
        >>> results = semantic_search("something sweet for breakfast", top_k=3)
        >>> for product_id, score in results:
        ...     print(f"Product {product_id}: {score:.3f} similarity")
    """
    model = get_model()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Generate query embedding
        query_embedding = model.encode(query, convert_to_numpy=True)
        
        # Get all product embeddings
        cursor.execute("SELECT product_id, embedding FROM product_embeddings")
        stored_embeddings = cursor.fetchall()
        
        if not stored_embeddings:
            raise ValueError("No product embeddings found. Run build_product_embeddings() first.")
        
        # Calculate similarities
        results = []
        for row in stored_embeddings:
            product_id = row['product_id']
            embedding_bytes = row['embedding']
            
            # Convert bytes back to numpy array
            product_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, product_embedding)
            
            if similarity >= threshold:
                results.append((product_id, float(similarity)))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply filters if provided
        if filters:
            results = apply_filters(cursor, results, filters)
        
        # Return top_k results
        return results[:top_k]
        
    finally:
        conn.close()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        a (np.ndarray): First vector
        b (np.ndarray): Second vector
        
    Returns:
        float: Similarity score between 0 and 1
    """
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def apply_filters(
    cursor: sqlite3.Cursor,
    results: List[Tuple[int, float]],
    filters: dict
) -> List[Tuple[int, float]]:
    """
    Apply additional filters to search results.
    
    Args:
        cursor: Database cursor
        results: List of (product_id, score) tuples
        filters: Filters to apply (max_price, is_organic, min_rating)
        
    Returns:
        list: Filtered results
    """
    if not filters:
        return results
    
    filtered = []
    product_ids = [r[0] for r in results]
    
    if not product_ids:
        return []
    
    # Build filter query
    placeholders = ','.join('?' * len(product_ids))
    conditions = [f"id IN ({placeholders})"]
    params = list(product_ids)
    
    if 'max_price' in filters and filters['max_price']:
        conditions.append("price <= ?")
        params.append(filters['max_price'])
    
    if 'is_organic' in filters and filters['is_organic'] is not None:
        conditions.append("is_organic = ?")
        params.append(1 if filters['is_organic'] else 0)
    
    where_clause = " AND ".join(conditions)
    cursor.execute(f"SELECT id FROM products WHERE {where_clause}", params)
    
    valid_ids = {row['id'] for row in cursor.fetchall()}
    
    # Filter results
    filtered = [(pid, score) for pid, score in results if pid in valid_ids]
    
    return filtered


# ==============================================================================
# Helper Functions
# ==============================================================================

def get_product_details(product_ids: List[int]) -> List[dict]:
    """
    Get full product details for a list of product IDs.
    
    Args:
        product_ids (list): List of product IDs
        
    Returns:
        list: List of product dictionaries
    """
    if not product_ids:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        placeholders = ','.join('?' * len(product_ids))
        cursor.execute(
            f"""SELECT id, name, category, price, description, is_organic
            FROM products WHERE id IN ({placeholders})""",
            product_ids
        )
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'id': row['id'],
                'name': row['name'],
                'category': row['category'],
                'price': row['price'],
                'description': row['description'],
                'is_organic': bool(row['is_organic'])
            })
        
        return products
        
    finally:
        conn.close()


def check_embeddings_exist() -> bool:
    """
    Check if product embeddings have been generated.
    
    Returns:
        bool: True if embeddings exist, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM product_embeddings")
        count = cursor.fetchone()['count']
        return count > 0
    except sqlite3.OperationalError:
        return False
    finally:
        conn.close()


# ==============================================================================
# CLI Testing Interface
# ==============================================================================

if __name__ == "__main__":
    """Test the vector search functionality."""
    print("=" * 70)
    print("ShopWise AI - Vector Search Testing")
    print("=" * 70)
    print()
    
    # Test 1: Check if embeddings exist
    print("TEST 1: Check Embeddings")
    print("-" * 70)
    if check_embeddings_exist():
        print("✓ Embeddings already exist")
    else:
        print("⚠ No embeddings found, building...")
        build_product_embeddings()
    print()
    
    # Test 2: Semantic search queries
    print("TEST 2: Semantic Search Queries")
    print("-" * 70)
    
    test_queries = [
        "something sweet for breakfast",
        "healthy cooking oil",
        "gift for a health-conscious friend",
        "protein-rich snack"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = semantic_search(query, top_k=3, threshold=0.2)
        
        if results:
            products = get_product_details([r[0] for r in results])
            for (pid, score), product in zip(results, products):
                print(f"  {score:.3f} - {product['name']} (${product['price']})")
        else:
            print("  (No results)")
    
    print()
    print("=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
