"""
ShopWise AI - Intelligent Shopping Agent Module

This module provides the core AI agent functionality for product search,
rating retrieval, order processing, and visual product recognition.

Architecture:
    - LangChain agent with specialized tools
    - SQLite database for product and order management
    - Multi-modal LLM support for image analysis
    - Integration with reviews API for rating data

Author: ShopWise Engineering Team
License: MIT
"""

import base64
import json
import os
import sqlite3
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq

import config

# Conditional imports based on feature flags
if config.ENABLE_CHECKPOINTING:
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        CHECKPOINTING_AVAILABLE = True
    except ImportError:
        CHECKPOINTING_AVAILABLE = False
        print("⚠ LangGraph checkpointing not available (install: pip install langgraph)")
else:
    CHECKPOINTING_AVAILABLE = False

from reviews_api import get_product_rating

# Conditional imports for optional features
if config.ENABLE_VECTOR_SEARCH:
    try:
        import vector_search
        VECTOR_SEARCH_AVAILABLE = True
    except ImportError:
        VECTOR_SEARCH_AVAILABLE = False
        print("⚠ Vector search not available (install: pip install sentence-transformers)")
else:
    VECTOR_SEARCH_AVAILABLE = False

# ==============================================================================
# Configuration & Initialization
# ==============================================================================

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")

# LLM Configuration - Support both local .env and Streamlit Cloud secrets
def get_api_key() -> str:
    """Get GROQ API key from environment variables."""
    return os.environ.get("GROQ_API_KEY", "")

api_key = get_api_key()

llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    max_retries=3,
    api_key=api_key
)

vision_llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0,
    max_retries=3,
    api_key=api_key
)


# ==============================================================================
# Database Utility Functions
# ==============================================================================

def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a database connection with optimized settings.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


# ==============================================================================
# Agent Tools
# ==============================================================================

@tool
def list_all_products() -> str:
    """
    List all available products in the store by name only.
    
    Use this tool when the user asks questions like:
    - "What products do you have?"
    - "List all items"
    - "Show me everything"
    - "What's available?"
    - "What can I buy?"
    
    Returns:
        str: Simple list of all product names
        
    Example:
        >>> list_all_products()
        'Available products: Organic Raw Honey, Olive Oil, Almonds, ...'
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM products ORDER BY name")
        products = cursor.fetchall()
        
        if not products:
            return "No products available at the moment."
        
        product_names = [row["name"] for row in products]
        
        # Format as a clean list
        response = f"We have {len(product_names)} products available:\n\n"
        response += "\n".join([f"• {name}" for name in product_names])
        
        return response
        
    finally:
        conn.close()


@tool
def search_products(
    query: str,
    max_price: Optional[float] = None,
    is_organic: Optional[bool] = None
) -> str:
    """
    Search the product database by keyword with optional filters.
    
    This tool searches across product names, descriptions, and categories,
    allowing filtering by maximum price and organic certification status.
    
    Args:
        query (str): Search keyword to match against name, description, and category
        max_price (Optional[float]): Maximum price filter (inclusive)
        is_organic (Optional[bool]): Filter by organic status (True/False)
    
    Returns:
        str: JSON array of matching products with complete product information
        
    Example:
        >>> search_products("honey", max_price=20.0, is_organic=True)
        '[{"id": 1, "name": "Organic Raw Honey", "price": 14.99, ...}]'
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT id, name, category, price, description, is_organic FROM products WHERE 1=1"
    params: List[Any] = []

    if query:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like])

    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)

    if is_organic is not None:
        sql += " AND is_organic = ?"
        params.append(1 if is_organic else 0)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    products = [
        {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "price": row["price"],
            "description": row["description"],
            "is_organic": bool(row["is_organic"]),
        }
        for row in rows
    ]
    
    return json.dumps(products, indent=2)


@tool
def get_rating(product_id: int) -> str:
    """
    Retrieve aggregated rating information for a specific product.
    
    Fetches the average customer rating and total number of reviews
    from the reviews database.
    
    Args:
        product_id (int): Unique product identifier
    
    Returns:
        str: JSON object containing product_id, average_rating, and review_count
        
    Example:
        >>> get_rating(1)
        '{"product_id": 1, "average_rating": 4.63, "review_count": 4}'
    """
    result = get_product_rating(product_id)
    return json.dumps(result, indent=2)


class CheckoutTool:
    """Stateful checkout tool that accesses user_id from runtime context."""
    
    def __init__(self):
        self.user_id = "guest"
    
    def set_user_id(self, user_id: str):
        """Set the user_id for this checkout session."""
        self.user_id = user_id
    
    def execute(self, product_id: int) -> str:
        """
        Process an order for the specified product.
        
        Creates an order record in the database and returns a confirmation
        message with order details. This should only be called after the user
        has explicitly confirmed their purchase intent.
        
        Args:
            product_id (int): Unique identifier of the product to order
        
        Returns:
            str: Order confirmation message or error message if product not found
            
        Example:
            >>> checkout_tool.execute(1)
            "Order #123 confirmed! 'Organic Raw Honey' has been successfully ordered..."
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"❌ Error: Product with ID {product_id} not found in our catalog."

        name, price = row["name"], row["price"]
        cursor.execute(
            "INSERT INTO orders (product_id, product_name, price, user_id) VALUES (?, ?, ?, ?)",
            (product_id, name, price, self.user_id),
        )
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return (
            f"✅ Order #{order_id} Confirmed!\n\n"
            f"Product: '{name}'\n"
            f"Price: ${price:.2f}\n\n"
            f"🚚 Estimated Delivery: 3-5 business days\n"
            f"📧 You'll receive a confirmation email shortly.\n\n"
            f"Thank you for shopping with ShopWise AI!"
        )


# Create a global checkout tool instance
_checkout_tool = CheckoutTool()


@tool
def checkout(product_id: int) -> str:
    """
    Process an order for the specified product.
    
    Creates an order record in the database and returns a confirmation
    message with order details. This should only be called after the user
    has explicitly confirmed their purchase intent.
    
    Args:
        product_id (int): Unique identifier of the product to order
    
    Returns:
        str: Order confirmation message or error message if product not found
        
    Example:
        >>> checkout(1)
        "Order #123 confirmed! 'Organic Raw Honey' has been successfully ordered..."
    """
    return _checkout_tool.execute(product_id)


@tool
def describe_product_image(image_path: str) -> str:
    """
    Analyze a product image using computer vision and extract key attributes.
    
    Uses a multi-modal LLM to identify product characteristics from an image,
    including product type, search keywords, organic status, and description.
    
    Args:
        image_path (str): File system path to the product image
    
    Returns:
        str: JSON object with extracted product attributes suitable for search
        
    Raises:
        FileNotFoundError: If the image file does not exist
        IOError: If the image cannot be read or processed
        
    Example:
        >>> describe_product_image("/tmp/honey.jpg")
        '{"product_type": "honey", "search_query": "honey", ...}'
    """
    if not os.path.exists(image_path):
        return json.dumps({"error": f"Image file not found: {image_path}"})
    
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
    except IOError as e:
        return json.dumps({"error": f"Failed to read image file: {str(e)}"})

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

    message = HumanMessage(content=[
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{image_data}"},
        },
        {
            "type": "text",
            "text": (
                "Analyze this product image and extract its key attributes. "
                "Return ONLY a valid JSON object with these fields:\n\n"
                "- product_type: the category of product (e.g., 'honey', 'olive oil', 'almonds')\n"
                "- search_query: a concise keyword for searching (e.g., 'honey', 'olive oil')\n"
                "- is_organic: true if the label indicates organic certification, false if not, null if unclear\n"
                "- description: a brief one-sentence description of the product\n\n"
                "Respond with ONLY the JSON object, no additional text."
            ),
        },
    ])

    try:
        response = vision_llm.invoke([message])
        return response.content
    except Exception as e:
        return json.dumps({"error": f"Vision model error: {str(e)}"})


@tool
def semantic_product_search(natural_query: str, top_k: int = 5) -> str:
    """
    Find products using semantic understanding rather than keyword matching.
    
    Use this when keyword search returns no results or when the user describes
    a feeling, use case, or vague intent rather than a specific product name.
    
    This tool uses AI embeddings to understand the meaning behind queries like:
    - "something for a healthy breakfast" → finds oats, granola, organic products
    - "gift for a foodie" → finds premium specialty items
    - "I want something sweet but not too expensive" → finds affordable treats
    - "something to put on toast" → finds honey, jam, nut butter
    
    Args:
        natural_query (str): Natural language description of what the user wants
        top_k (int): Maximum number of results to return (default: 5)
    
    Returns:
        str: JSON array of matching products with similarity scores
        
    Example:
        >>> semantic_product_search("healthy breakfast option", 3)
        '[{"id": 17, "name": "Organic Quinoa", "score": 0.78, ...}]'
    """
    if not VECTOR_SEARCH_AVAILABLE:
        return json.dumps({"error": "Semantic search not available. Feature disabled."})
    
    try:
        # Perform semantic search
        results = vector_search.semantic_search(
            natural_query,
            top_k=top_k,
            threshold=config.VECTOR_SIMILARITY_THRESHOLD
        )
        
        if not results:
            return json.dumps([])
        
        # Get product details
        product_ids = [r[0] for r in results]
        products = vector_search.get_product_details(product_ids)
        
        # Add similarity scores
        score_map = {pid: score for pid, score in results}
        for product in products:
            product['semantic_score'] = score_map[product['id']]
            product['search_type'] = 'semantic'
        
        return json.dumps(products, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Semantic search error: {str(e)}"})


# Collect all tools
ALL_TOOLS = [list_all_products, search_products, get_rating, checkout, describe_product_image]

# Add semantic search if available
if VECTOR_SEARCH_AVAILABLE:
    ALL_TOOLS.append(semantic_product_search)


# ==============================================================================
# Agent System Prompt
# ==============================================================================

AGENT_SYSTEM_PROMPT = """You are ShopWise AI, a professional and intelligent shopping assistant.
Your role is to help customers find products, compare ratings, and complete purchases seamlessly.

CORE PRINCIPLES:
- Be professional, friendly, and concise
- Always prioritize user preferences and requirements
- Provide clear, well-formatted product information
- Never proceed with checkout without explicit user confirmation
- Handle errors gracefully with helpful messages

TOOL SELECTION STRATEGY:
- Use semantic_product_search when:
  * User describes a vague need ("something for breakfast", "healthy snack")
  * User describes a use case ("gift for foodie", "put on toast")
  * User expresses a feeling or preference without specific keywords
  * Keyword search returns no results
- Use search_products when:
  * User mentions specific product names or brands
  * User provides exact keywords (honey, coffee, almonds)
  * User wants to filter by price, organic, or rating
  
WORKFLOW PROTOCOLS:

═══════════════════════════════════════════════════════════════════
1. IMAGE-BASED SEARCH (when user provides an image path)
═══════════════════════════════════════════════════════════════════
   Step 1: Call describe_product_image(image_path) to analyze the image
   Step 2: Extract search_query and is_organic from the JSON response
   Step 3: Call search_products(search_query, is_organic=is_organic)
   Step 4: Continue with PRODUCT BROWSING workflow (see below)

═══════════════════════════════════════════════════════════════════
2. PRODUCT BROWSING (when user describes what they want)
═══════════════════════════════════════════════════════════════════
   Step 1: Decide which search tool to use:
           - Vague/descriptive query → semantic_product_search
           - Specific keywords → search_products
   
   Step 2: For EACH product found, call get_rating(product_id)
   
   Step 3: Filter results by minimum rating if user specified one
   
   Step 4: Present qualified products in this EXACT format:
   
           Found X products matching your criteria:
           
           #1. [Product Name] (ID:[id]) — $[price] ⭐[rating]/5.0 ([review_count] reviews) — [organic/non-organic]
              [Brief description]
           
           #2. [Product Name] (ID:[id]) — $[price] ⭐[rating]/5.0 ([review_count] reviews) — [organic/non-organic]
              [Brief description]
           
           Would you like to order any of these? Just let me know the number or say "yes" for #1.
   
   FORMATTING RULES:
   - Use plain text, no markdown code blocks
   - Always include (ID:[number]) for later reference
   - Add blank line between products
   - Show organic status clearly
   - If only 1 product qualifies, still show it and ask for confirmation
   - If results came from semantic_product_search, mention "Found using semantic matching"
   
   Step 5: DO NOT call checkout() at this stage - wait for user confirmation

═══════════════════════════════════════════════════════════════════
3. ORDER PROCESSING (when user confirms purchase)
═══════════════════════════════════════════════════════════════════
   User confirmation phrases include:
   - "yes", "sure", "go ahead", "okay", "confirm"
   - "order number X", "get me #X", "I'll take the first one"
   - "buy it", "purchase", "checkout"
   
   Step 1: Identify which product the user wants:
           - If you listed multiple products and user says a number, use that (ID:X)
           - If you listed one product and user says "yes", use that (ID:X)
           - ALWAYS extract the ID from your previous message's (ID:X) notation
   
   Step 2: Call checkout(product_id) with the correct product ID
   
   Step 3: Relay the confirmation message to the user

═══════════════════════════════════════════════════════════════════
ERROR HANDLING:
═══════════════════════════════════════════════════════════════════
- If no products match: Suggest relaxing filters or try semantic search
- If image analysis fails: Ask user to describe the product instead
- If product ID not found: Apologize and show available options again
- Never guess product IDs - always use (ID:X) from your previous response

RESPONSE TONE:
- Professional yet approachable
- Use emojis sparingly for visual clarity (✅, ❌, 🚚, ⭐)
- Keep responses concise but informative
- Always confirm actions before executing them
"""


def inject_memory_context(user_context: str) -> str:
    """
    Inject user memory context into the system prompt.
    
    Args:
        user_context (str): User personalization context
        
    Returns:
        str: Enhanced system prompt with user context
    """
    if not user_context:
        return AGENT_SYSTEM_PROMPT
    
    enhanced_prompt = f"""{AGENT_SYSTEM_PROMPT}

═══════════════════════════════════════════════════════════════════
PERSONALIZATION - USER HISTORY & PREFERENCES:
═══════════════════════════════════════════════════════════════════
{user_context}

Use this context to:
- Suggest similar products to what they've ordered before
- Respect their price preferences
- Consider their organic preference
- Reference their past searches when relevant
═══════════════════════════════════════════════════════════════════
"""
    return enhanced_prompt


# ==============================================================================
# Agent Instance
# ==============================================================================

# Initialize checkpointer if enabled
checkpointer = None
if config.ENABLE_CHECKPOINTING and CHECKPOINTING_AVAILABLE:
    try:
        checkpointer = SqliteSaver.from_conn_string(DB_PATH)
        print("✓ LangGraph checkpointing enabled")
    except Exception as e:
        print(f"⚠ Could not initialize checkpointer: {e}")
        checkpointer = None

# Create agent with optional checkpointing
if checkpointer:
    # Enhanced agent with stateful memory
    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        checkpointer=checkpointer,
        state_modifier=AGENT_SYSTEM_PROMPT
    )
else:
    # Standard agent without checkpointing
    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        state_modifier=AGENT_SYSTEM_PROMPT
    )


def create_personalized_agent(user_context: str = ""):
    """
    Create an agent instance with personalized system prompt.
    
    Args:
        user_context (str): User personalization context to inject
        
    Returns:
        Agent: Configured agent instance
    """
    enhanced_prompt = inject_memory_context(user_context)
    
    if checkpointer:
        return create_react_agent(
            model=llm,
            tools=ALL_TOOLS,
            checkpointer=checkpointer,
            state_modifier=enhanced_prompt
        )
    else:
        return create_react_agent(
            model=llm,
            tools=ALL_TOOLS,
            state_modifier=enhanced_prompt
        )


def set_user_context(user_id: str):
    """
    Set the user context for the current agent session.
    
    Args:
        user_id (str): User ID to associate with orders
    """
    global _checkout_tool
    _checkout_tool.set_user_id(user_id)


# ==============================================================================
# CLI Testing Interface
# ==============================================================================

if __name__ == "__main__":
    """
    Command-line interface for testing the shopping agent.
    Run this module directly to test agent functionality without the UI.
    """
    print("=" * 70)
    print("ShopWise AI - Agent Testing Interface")
    print("=" * 70)
    print()
    
    test_query = {
        "messages": [
            {
                "role": "user",
                "content": "I want to buy organic honey with 4.5+ rating and less than $20 price."
            }
        ]
    }
    
    print(f"Test Query: {test_query['messages'][0]['content']}")
    print("\n" + "-" * 70 + "\n")
    
    result = agent.invoke(test_query)
    response = result["messages"][-1].content
    
    print("Agent Response:")
    print(response)
    print("\n" + "=" * 70)
