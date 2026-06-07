"""
ShopWise AI - Authentication Manager

Production-grade authentication system using SQLite and bcrypt.
Handles user registration, login, sessions, and rate limiting.

Author: ShopWise Engineering Team
License: MIT
"""

import bcrypt
import sqlite3
import uuid
import re
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

# ==============================================================================
# Configuration
# ==============================================================================

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")

# Security settings
BCRYPT_WORK_FACTOR = 12
SESSION_EXPIRY_DAYS = 7
SESSION_EXPIRY_DAYS_REMEMBER = 30
MAX_LOGIN_ATTEMPTS = 5
RATE_LIMIT_WINDOW_MINUTES = 15

# Password requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_NUMBER = True
PASSWORD_REQUIRE_SPECIAL = True

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


# ==============================================================================
# Authentication Manager Class
# ==============================================================================

class AuthManager:
    """
    Manages user authentication, sessions, and security.
    
    Provides secure user registration, login, session management,
    and rate limiting to prevent brute force attacks.
    """
    
    def __init__(self, db_path: str = DB_PATH):
        """
        Initialize the authentication manager.
        
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
    
    # ==========================================================================
    # Registration
    # ==========================================================================
    
    def register(
        self,
        email: str,
        username: str,
        password: str,
        full_name: str = ""
    ) -> Dict[str, Any]:
        """
        Register a new user account.
        
        Args:
            email (str): User email address (must be unique)
            username (str): Username (must be unique)
            password (str): Plain text password (will be hashed)
            full_name (str): User's full name (optional)
            
        Returns:
            dict: {success: bool, user_id: str, error: str}
            
        Example:
            >>> am = AuthManager()
            >>> result = am.register("user@example.com", "john_doe", "Pass123!", "John Doe")
            >>> if result['success']:
            ...     print(f"User created: {result['user_id']}")
        """
        # Validate email format
        if not self._validate_email(email):
            return {"success": False, "user_id": None, "error": "Invalid email format"}
        
        # Validate password strength
        password_valid, password_error = self._validate_password(password)
        if not password_valid:
            return {"success": False, "user_id": None, "error": password_error}
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email.lower(),))
            if cursor.fetchone():
                return {"success": False, "user_id": None, "error": "Email already registered"}
            
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return {"success": False, "user_id": None, "error": "Username already taken"}
            
            # Generate user ID
            user_id = str(uuid.uuid4())
            
            # Generate salt and hash password
            salt = bcrypt.gensalt(rounds=BCRYPT_WORK_FACTOR)
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            # Get avatar initial
            avatar_initial = (full_name[0].upper() if full_name else username[0].upper())
            
            # Insert user
            cursor.execute(
                """INSERT INTO users 
                (id, username, email, password_hash, salt, full_name, avatar_initial, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                (user_id, username, email.lower(), password_hash, salt, full_name, avatar_initial)
            )
            
            # Create user profile for memory/personalization
            cursor.execute(
                """INSERT INTO user_profiles (user_id, display_name, created_at, last_seen)
                VALUES (?, ?, datetime('now'), datetime('now'))""",
                (user_id, username)
            )
            
            conn.commit()
            
            return {
                "success": True,
                "user_id": user_id,
                "error": None
            }
            
        except sqlite3.IntegrityError as e:
            return {"success": False, "user_id": None, "error": f"Database error: {str(e)}"}
        except Exception as e:
            return {"success": False, "user_id": None, "error": f"Registration failed: {str(e)}"}
        finally:
            conn.close()
    
    # ==========================================================================
    # Login
    # ==========================================================================
    
    def login(
        self,
        email: str,
        password: str,
        ip_address: str = "unknown",
        remember_me: bool = False
    ) -> Dict[str, Any]:
        """
        Authenticate user and create session.
        
        Args:
            email (str): User email
            password (str): Plain text password
            ip_address (str): Client IP address for logging
            remember_me (bool): Extend session to 30 days if True
            
        Returns:
            dict: {success: bool, session_token: str, user_id: str, 
                   username: str, full_name: str, avatar_initial: str, error: str}
                   
        Example:
            >>> result = am.login("user@example.com", "Pass123!")
            >>> if result['success']:
            ...     session_token = result['session_token']
        """
        # Check rate limiting
        if self.is_rate_limited(email):
            self._log_login_attempt(email, ip_address, success=False)
            return {
                "success": False,
                "session_token": None,
                "user_id": None,
                "username": None,
                "full_name": None,
                "avatar_initial": None,
                "error": "Too many failed attempts. Please try again in 15 minutes."
            }
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get user by email
            cursor.execute(
                """SELECT id, username, email, password_hash, full_name, avatar_initial, is_active
                FROM users WHERE email = ?""",
                (email.lower(),)
            )
            user = cursor.fetchone()
            
            if not user:
                self._log_login_attempt(email, ip_address, success=False)
                return {
                    "success": False,
                    "session_token": None,
                    "user_id": None,
                    "username": None,
                    "full_name": None,
                    "avatar_initial": None,
                    "error": "Invalid email or password"
                }
            
            # Check if account is active
            if not user['is_active']:
                return {
                    "success": False,
                    "session_token": None,
                    "user_id": None,
                    "username": None,
                    "full_name": None,
                    "avatar_initial": None,
                    "error": "Account is deactivated"
                }
            
            # Verify password
            password_hash = user['password_hash']
            if isinstance(password_hash, str):
                password_hash = password_hash.encode('utf-8')
            
            if not bcrypt.checkpw(password.encode('utf-8'), password_hash):
                self._log_login_attempt(email, ip_address, success=False)
                return {
                    "success": False,
                    "session_token": None,
                    "user_id": None,
                    "username": None,
                    "full_name": None,
                    "avatar_initial": None,
                    "error": "Invalid email or password"
                }
            
            # Create session
            session_token = str(uuid.uuid4())
            expiry_days = SESSION_EXPIRY_DAYS_REMEMBER if remember_me else SESSION_EXPIRY_DAYS
            expires_at = datetime.now() + timedelta(days=expiry_days)
            
            cursor.execute(
                """INSERT INTO sessions 
                (session_token, user_id, expires_at, ip_address, is_active)
                VALUES (?, ?, ?, ?, 1)""",
                (session_token, user['id'], expires_at.isoformat(), ip_address)
            )
            
            # Update last login
            cursor.execute(
                """UPDATE users 
                SET last_login = datetime('now'), login_count = login_count + 1
                WHERE id = ?""",
                (user['id'],)
            )
            
            conn.commit()
            
            # Log successful attempt
            self._log_login_attempt(email, ip_address, success=True)
            
            return {
                "success": True,
                "session_token": session_token,
                "user_id": user['id'],
                "username": user['username'],
                "full_name": user['full_name'] or user['username'],
                "avatar_initial": user['avatar_initial'],
                "email": user['email'],
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "session_token": None,
                "user_id": None,
                "username": None,
                "full_name": None,
                "avatar_initial": None,
                "error": f"Login failed: {str(e)}"
            }
        finally:
            conn.close()
    
    # ==========================================================================
    # Session Management
    # ==========================================================================
    
    def verify_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify session token and return user data.
        
        Args:
            session_token (str): Session token to verify
            
        Returns:
            dict: User data if valid, None if invalid/expired
            
        Example:
            >>> user = am.verify_session(session_token)
            >>> if user:
            ...     print(f"Authenticated as: {user['username']}")
        """
        if not session_token:
            return None
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT s.session_token, s.user_id, s.expires_at, s.is_active,
                u.username, u.email, u.full_name, u.avatar_initial
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ? AND s.is_active = 1""",
                (session_token,)
            )
            
            session = cursor.fetchone()
            
            if not session:
                return None
            
            # Check expiry
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.now() > expires_at:
                # Deactivate expired session
                cursor.execute(
                    "UPDATE sessions SET is_active = 0 WHERE session_token = ?",
                    (session_token,)
                )
                conn.commit()
                return None
            
            return {
                "user_id": session['user_id'],
                "username": session['username'],
                "email": session['email'],
                "full_name": session['full_name'] or session['username'],
                "avatar_initial": session['avatar_initial'],
                "session_token": session_token
            }
            
        finally:
            conn.close()
    
    def logout(self, session_token: str) -> bool:
        """
        Invalidate a session token.
        
        Args:
            session_token (str): Session token to invalidate
            
        Returns:
            bool: True if successful
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE sessions SET is_active = 0 WHERE session_token = ?",
                (session_token,)
            )
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()
    
    def cleanup_expired_sessions(self) -> int:
        """
        Delete expired sessions from database.
        
        Returns:
            int: Number of sessions cleaned up
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM sessions WHERE datetime(expires_at) < datetime('now')"
            )
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        finally:
            conn.close()
    
    # ==========================================================================
    # User Profile Management
    # ==========================================================================
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete user profile.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: User profile data or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT id, username, email, full_name, avatar_initial,
                created_at, last_login, login_count
                FROM users WHERE id = ?""",
                (user_id,)
            )
            
            user = cursor.fetchone()
            if not user:
                return None
            
            return dict(user)
            
        finally:
            conn.close()
    
    def update_profile(self, user_id: str, full_name: str) -> bool:
        """
        Update user profile.
        
        Args:
            user_id (str): User ID
            full_name (str): New full name
            
        Returns:
            bool: True if successful
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            avatar_initial = full_name[0].upper() if full_name else ""
            cursor.execute(
                "UPDATE users SET full_name = ?, avatar_initial = ? WHERE id = ?",
                (full_name, avatar_initial, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
        finally:
            conn.close()
    
    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """
        Change user password.
        
        Args:
            user_id (str): User ID
            old_password (str): Current password
            new_password (str): New password
            
        Returns:
            dict: {success: bool, error: str}
        """
        # Validate new password
        password_valid, password_error = self._validate_password(new_password)
        if not password_valid:
            return {"success": False, "error": password_error}
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current password hash
            cursor.execute(
                "SELECT password_hash FROM users WHERE id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Verify old password
            password_hash = user['password_hash']
            if isinstance(password_hash, str):
                password_hash = password_hash.encode('utf-8')
            
            if not bcrypt.checkpw(old_password.encode('utf-8'), password_hash):
                return {"success": False, "error": "Current password is incorrect"}
            
            # Hash new password
            salt = bcrypt.gensalt(rounds=BCRYPT_WORK_FACTOR)
            new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
            
            # Update password
            cursor.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (new_password_hash, salt, user_id)
            )
            conn.commit()
            
            return {"success": True, "error": None}
            
        except Exception as e:
            return {"success": False, "error": f"Password change failed: {str(e)}"}
        finally:
            conn.close()
    
    # ==========================================================================
    # Rate Limiting
    # ==========================================================================
    
    def is_rate_limited(self, email: str) -> bool:
        """
        Check if email is rate limited due to failed login attempts.
        
        Args:
            email (str): Email to check
            
        Returns:
            bool: True if rate limited
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff = datetime.now() - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
            
            cursor.execute(
                """SELECT COUNT(*) as failed_count
                FROM login_attempts
                WHERE email = ? AND success = 0 AND datetime(attempted_at) > datetime(?)""",
                (email.lower(), cutoff.isoformat())
            )
            
            result = cursor.fetchone()
            return result['failed_count'] >= MAX_LOGIN_ATTEMPTS
            
        finally:
            conn.close()
    
    def _log_login_attempt(self, email: str, ip_address: str, success: bool) -> None:
        """
        Log a login attempt.
        
        Args:
            email (str): Email attempted
            ip_address (str): IP address
            success (bool): Whether attempt was successful
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO login_attempts (email, ip_address, success)
                VALUES (?, ?, ?)""",
                (email.lower(), ip_address, 1 if success else 0)
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()
    
    # ==========================================================================
    # User Data
    # ==========================================================================
    
    def get_user_orders(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's recent orders.
        
        Args:
            user_id (str): User ID
            limit (int): Maximum number of orders
            
        Returns:
            list: List of order dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT id, product_id, product_name, price, ordered_at
                FROM orders
                WHERE user_id = ?
                ORDER BY ordered_at DESC
                LIMIT ?""",
                (user_id, limit)
            )
            
            return [dict(row) for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: User statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get order count
            cursor.execute(
                "SELECT COUNT(*) as count FROM orders WHERE user_id = ?",
                (user_id,)
            )
            order_count = cursor.fetchone()['count']
            
            # Get search count
            cursor.execute(
                "SELECT COUNT(*) as count FROM search_history WHERE user_id = ?",
                (user_id,)
            )
            search_count = cursor.fetchone()['count']
            
            return {
                "order_count": order_count,
                "search_count": search_count
            }
            
        finally:
            conn.close()
    
    # ==========================================================================
    # Validation Helpers
    # ==========================================================================
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        return bool(EMAIL_REGEX.match(email))
    
    def _validate_password(self, password: str) -> tuple:
        """
        Validate password strength.
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        if len(password) < PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
        
        if PASSWORD_REQUIRE_NUMBER and not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, ""
    
    def check_username_available(self, username: str) -> bool:
        """
        Check if username is available.
        
        Args:
            username (str): Username to check
            
        Returns:
            bool: True if available
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            return cursor.fetchone() is None
        finally:
            conn.close()


# ==============================================================================
# Module Functions
# ==============================================================================

def get_auth_manager() -> AuthManager:
    """Get an AuthManager instance."""
    return AuthManager()


# ==============================================================================
# CLI Testing
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ShopWise AI - Authentication Manager Testing")
    print("=" * 70)
    print()
    
    am = AuthManager()
    
    # Test registration
    print("TEST 1: User Registration")
    print("-" * 70)
    result = am.register(
        "test@shopwise.ai",
        "testuser",
        "TestPass123!",
        "Test User"
    )
    print(f"Registration: {'✓ Success' if result['success'] else '✗ Failed'}")
    if not result['success']:
        print(f"Error: {result['error']}")
    print()
    
    # Test login
    print("TEST 2: User Login")
    print("-" * 70)
    result = am.login("test@shopwise.ai", "TestPass123!")
    print(f"Login: {'✓ Success' if result['success'] else '✗ Failed'}")
    if result['success']:
        print(f"Session token: {result['session_token'][:20]}...")
        session_token = result['session_token']
        user_id = result['user_id']
    print()
    
    # Test session verification
    if result['success']:
        print("TEST 3: Session Verification")
        print("-" * 70)
        user = am.verify_session(session_token)
        print(f"Session valid: {'✓ Yes' if user else '✗ No'}")
        if user:
            print(f"Username: {user['username']}")
        print()
    
    print("=" * 70)
    print("✅ Tests completed!")
    print("=" * 70)
