"""
ShopWise AI - Authentication UI Module

Streamlit-based authentication interface with login, registration, and guest access.
Styled to match the existing purple-blue gradient theme.

Author: ShopWise Engineering Team
License: MIT
"""

import streamlit as st
import re
import uuid
from typing import Optional, Dict, Any
from auth_manager import AuthManager

# ==============================================================================
# Password Strength Calculation
# ==============================================================================

def calculate_password_strength(password: str) -> int:
    """
    Calculate password strength on a scale of 0-3.
    
    Args:
        password (str): Password to evaluate
        
    Returns:
        int: Strength score (0=weak, 1=weak, 2=medium, 3=strong)
    """
    score = 0
    
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if re.search(r'\d', password) and re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    if re.search(r'[A-Z]', password) and re.search(r'[a-z]', password):
        score += 1
    
    return min(score, 3)


# ==============================================================================
# Authentication Page Renderer
# ==============================================================================

def render_auth_page() -> Optional[Dict[str, Any]]:
    """
    Render the authentication page with login, register, and guest options.
    
    Returns:
        dict: User data if authenticated/guest, None if still on auth page
            - For authenticated: {success, session_token, user_id, username, full_name, email, avatar_initial}
            - For guest: {is_guest: True, user_id: str}
    """
    
    # Custom CSS for auth page - Luxury Editorial / Premium SaaS
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

    #MainMenu, footer, header, .stDeployButton { display: none !important; }

    .stApp {
      background: var(--bg-surface) !important;
      font-family: var(--font-ui);
      color: var(--text-primary);
    }

    /* Auth page layout */
    .block-container {
      padding: 0 !important;
      max-width: 100% !important;
      min-height: 100vh !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
    }
    section.main > div {
      background: transparent !important;
      min-height: 100vh !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
    }
    .element-container { margin: 0 !important; width: 100%; }

    .auth-container {
      max-width: 460px;
      width: 100%;
      margin: auto !important;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--r-lg);
      padding: 2.5rem;
      box-shadow: var(--shadow-md);
    }

    .auth-logo {
      text-align: center;
      margin-bottom: 2.5rem;
    }
    .auth-logo .icon { font-size: 2.8rem; display: block; margin-bottom: 0.75rem; }
    .auth-logo .wordmark {
      font-family: var(--font-display);
      font-size: 2rem;
      color: var(--text-primary);
      letter-spacing: -0.02em;
      display: block;
      font-weight: 600;
    }
    .auth-logo .tagline {
      font-size: 0.875rem;
      color: var(--text-secondary);
      display: block;
      margin-top: 0.5rem;
      font-weight: 400;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
      background: transparent !important;
      border-bottom: 1px solid var(--border);
      gap: 0 !important;
      justify-content: center !important;
    }
    .stTabs [data-baseweb="tab"] {
      background: transparent !important;
      border-radius: 0 !important;
      font-family: var(--font-ui) !important;
      font-size: 0.9rem !important;
      font-weight: 500 !important;
      color: var(--text-muted) !important;
      padding: 0.85rem 1.6rem !important;
      border-bottom: 2px solid transparent;
      margin-bottom: -1px;
      transition: all 0.15s ease;
      flex: 1 !important;
      text-align: center !important;
    }
    .stTabs [aria-selected="true"] {
      color: var(--accent) !important;
      border-bottom: 2px solid var(--accent) !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
      background: var(--bg-card) !important;
      border: none !important;
      padding: 2rem 0 !important;
    }

    /* Inputs */
    .stTextInput input {
      background: var(--bg-card) !important;
      border: 1px solid var(--border) !important;
      border-radius: var(--r-sm) !important;
      color: var(--text-primary) !important;
      font-family: var(--font-ui) !important;
      font-size: 0.9375rem !important;
      padding: 0.625rem 0.875rem !important;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .stTextInput input:focus {
      border-color: var(--accent) !important;
      box-shadow: 0 0 0 3px var(--accent-light) !important;
      outline: none !important;
    }
    .stTextInput input::placeholder { color: var(--text-muted) !important; }
    .stTextInput label { color: var(--text-secondary) !important; font-family: var(--font-ui) !important; font-size: 0.875rem !important; font-weight: 500 !important; }

    /* Buttons */
    .stButton button[kind="primary"] {
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
    .stButton button:not([kind="primary"]) {
      background: var(--bg-card) !important;
      color: var(--text-secondary) !important;
      border: 1px solid var(--border) !important;
      border-radius: var(--r-sm) !important;
      font-family: var(--font-ui) !important;
      font-weight: 500 !important;
      transition: all 0.15s ease !important;
    }
    .stButton button:not([kind="primary"]):hover {
      border-color: var(--accent) !important;
      color: var(--accent) !important;
    }

    /* Progress */
    .stProgress > div > div { background: #e5e7eb !important; border-radius: 99px !important; }
    .stProgress > div > div > div { border-radius: 99px !important; transition: width 0.3s ease, background-color 0.3s ease !important; }

    /* Checkbox */
    .stCheckbox label { color: var(--text-primary) !important; font-family: var(--font-ui) !important; font-size: 0.9375rem !important; font-weight: 400 !important; }

    /* Alerts */
    .stAlert { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--r-sm) !important; color: var(--text-primary) !important; font-family: var(--font-ui) !important; box-shadow: var(--shadow-sm) !important; }

    /* Caption */
    .stMarkdown small, .stCaption { color: var(--text-secondary) !important; font-family: var(--font-ui) !important; }

    /* Form submit buttons (inside st.form) */
    [data-testid="stFormSubmitButton"] button {
      background: var(--accent) !important;
      color: #ffffff !important;
      border: none !important;
      border-radius: var(--r-sm) !important;
      font-family: var(--font-ui) !important;
      font-weight: 600 !important;
      transition: all 0.15s ease !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Container with no columns - centered card
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="auth-logo">
      <span class="icon">🛍️</span>
      <span class="wordmark">ShopWise AI</span>
      <span class="tagline">Your Intelligent Shopping Companion</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🔑 Login", "🚀 Register", "👤 Guest"])
    
    # ==========================================================================
    # Login Tab
    # ==========================================================================
    with tab1:
        st.markdown("### Sign In to Your Account")
        
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="your.email@example.com")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me for 30 days")
            
            col1, col2 = st.columns([3, 2])
            with col1:
                submit = st.form_submit_button("🔑 Sign In", use_container_width=True, type="primary")
            with col2:
                guest_login = st.form_submit_button("Continue as Guest", use_container_width=True)
            
            if submit:
                if not email or not password:
                    st.error("❌ Please enter both email and password")
                else:
                    am = AuthManager()
                    result = am.login(email, password, remember_me=remember_me)
                    
                    if result['success']:
                        st.success("✅ Login successful!")
                        st.balloons()
                        st.markdown('</div>', unsafe_allow_html=True)
                        return result
                    else:
                        st.error(f"❌ {result['error']}")
            
            if guest_login:
                st.markdown('</div>', unsafe_allow_html=True)
                return {
                    "is_guest": True,
                    "user_id": f"guest_{str(uuid.uuid4())[:8]}",
                    "username": "Guest",
                    "full_name": "Guest User",
                    "avatar_initial": "G"
                }
        
        st.markdown("---")
        st.caption("🔒 Forgot password? Contact support")
    
    # ==========================================================================
    # Register Tab
    # ==========================================================================
    with tab2:
        st.markdown("### Create Your Account")
        
        with st.form("register_form"):
            full_name = st.text_input("👤 Full Name", placeholder="John Doe")
            email = st.text_input("📧 Email", placeholder="your.email@example.com", key="reg_email")
            username = st.text_input("🆔 Username", placeholder="johndoe", key="reg_username")
            
            # Username availability check
            if username and len(username) >= 3:
                am = AuthManager()
                if am.check_username_available(username):
                    st.success("✅ Username available")
                else:
                    st.error("❌ Username already taken")
            
            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("🔒 Password", type="password", placeholder="Min 8 characters", key="reg_pass")
            with col2:
                confirm_password = st.text_input("🔒 Confirm", type="password", placeholder="Re-enter password", key="reg_confirm")
            
            # Password strength indicator
            if password:
                strength = calculate_password_strength(password)
                
                if strength <= 1:
                    st.progress(0.33, text=f"🔴 Weak password")
                elif strength == 2:
                    st.progress(0.66, text=f"🟡 Medium password")
                else:
                    st.progress(1.0, text=f"🟢 Strong password")
                
                st.caption("Password must contain: 8+ characters, 1 number, 1 special character")
            
            submit_register = st.form_submit_button("🚀 Create Account", use_container_width=True, type="primary")
            
            if submit_register:
                # Validation
                if not all([full_name, email, username, password, confirm_password]):
                    st.error("❌ Please fill in all fields")
                elif password != confirm_password:
                    st.error("❌ Passwords do not match")
                elif len(password) < 8:
                    st.error("❌ Password must be at least 8 characters")
                else:
                    # Register user
                    am = AuthManager()
                    result = am.register(email, username, password, full_name)
                    
                    if result['success']:
                        st.success("✅ Account created successfully!")
                        st.balloons()
                        
                        # Auto-login
                        login_result = am.login(email, password)
                        if login_result['success']:
                            st.markdown('</div>', unsafe_allow_html=True)
                            return login_result
                    else:
                        st.error(f"❌ {result['error']}")
        
        st.markdown("---")
        st.caption("✅ By registering, you agree to our Terms of Service")
    
    # ==========================================================================
    # Guest Tab
    # ==========================================================================
    with tab3:
        st.markdown("### Continue Without Account")
        
        st.markdown("""
        <div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:var(--r-md);padding:1.5rem;margin-bottom:1.5rem;box-shadow:var(--shadow-sm);">
          <div style="margin-bottom:1rem;font-family:var(--font-ui);font-size:0.75rem;
                      text-transform:uppercase;letter-spacing:0.1em;color:var(--text-muted);font-weight:600;">
            Guest Mode
          </div>
          <div style="display:flex;flex-direction:column;gap:0.625rem;font-size:0.9375rem;color:var(--text-primary);">
            <div><span style="color:var(--accent);">✓</span> Full shopping experience</div>
            <div><span style="color:var(--accent);">✓</span> Product search and orders</div>
            <div><span style="color:var(--accent);">✓</span> AI assistant access</div>
            <div style="margin-top:0.75rem;padding-top:0.75rem;border-top:1px solid var(--border);">
              <span style="color:var(--warning);">⚠</span>
              <span style="color:var(--text-secondary);"> Preferences not saved across sessions</span>
            </div>
            <div>
              <span style="color:var(--warning);">⚠</span>
              <span style="color:var(--text-secondary);"> No order history</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        if st.button("👤 Continue as Guest", use_container_width=True, type="primary"):
            st.markdown('</div>', unsafe_allow_html=True)
            return {
                "is_guest": True,
                "user_id": f"guest_{str(uuid.uuid4())[:8]}",
                "username": "Guest",
                "full_name": "Guest User",
                "avatar_initial": "G",
                "email": None
            }
        
        st.markdown("---")
        st.caption("💡 Create a free account to unlock personalized features!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    return None


# ==============================================================================
# User Profile Modal
# ==============================================================================

def render_profile_modal(user: Dict[str, Any]) -> None:
    """
    Render user profile editing modal.
    
    Args:
        user (dict): Current user data
    """
    st.markdown("### ⚙️ Profile Settings")
    
    am = AuthManager()
    
    with st.form("profile_form"):
        new_name = st.text_input("Full Name", value=user.get('full_name', ''))
        submit = st.form_submit_button("💾 Save Changes", type="primary")
        
        if submit:
            if am.update_profile(user['user_id'], new_name):
                st.success("✅ Profile updated!")
                st.session_state.user['full_name'] = new_name
                st.rerun()
            else:
                st.error("❌ Failed to update profile")


# ==============================================================================
# Password Change Modal
# ==============================================================================

def render_password_modal(user: Dict[str, Any]) -> None:
    """
    Render password change modal.
    
    Args:
        user (dict): Current user data
    """
    st.markdown("### 🔑 Change Password")
    
    am = AuthManager()
    
    with st.form("password_form"):
        old_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submit = st.form_submit_button("🔐 Change Password", type="primary")
        
        if submit:
            if not all([old_password, new_password, confirm_password]):
                st.error("❌ Please fill in all fields")
            elif new_password != confirm_password:
                st.error("❌ New passwords do not match")
            else:
                result = am.change_password(user['user_id'], old_password, new_password)
                if result['success']:
                    st.success("✅ Password changed successfully!")
                else:
                    st.error(f"❌ {result['error']}")


# ==============================================================================
# Orders Modal
# ==============================================================================

def render_orders_modal(user: Dict[str, Any]) -> None:
    """
    Render user orders history modal.
    
    Args:
        user (dict): Current user data
    """
    st.markdown("### 📦 Your Orders")
    
    am = AuthManager()
    orders = am.get_user_orders(user['user_id'], limit=10)
    
    if not orders:
        st.info("No orders yet. Start shopping!")
    else:
        for order in orders:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"**{order['product_name']}**")
                with col2:
                    st.markdown(f"${order['price']:.2f}")
                with col3:
                    st.markdown(f"_{order['ordered_at'][:10]}_")
                st.divider()


# ==============================================================================
# Testing
# ==============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="Auth UI Test", layout="centered")
    
    result = render_auth_page()
    
    if result:
        st.success("Authentication successful!")
        st.json(result)
