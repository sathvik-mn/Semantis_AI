"""
Database Module for API Key Storage and User Management
Stores API keys with user information and plan details for future subscription management.
"""
import sqlite3
import os
import json
from typing import Optional, Dict, List
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "cache_data/api_keys.db"

def ensure_db_dir():
    """Ensure database directory exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

@contextmanager
def get_db_connection():
    """Get database connection with context manager."""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize database tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                name TEXT,
                password_hash TEXT,
                email_verified BOOLEAN DEFAULT 0,
                is_admin BOOLEAN DEFAULT 0,
                last_login_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add is_admin column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0')
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        # Add openai_api_key_encrypted column if it doesn't exist (for BYOK)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN openai_api_key_encrypted TEXT')
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        # API keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT UNIQUE NOT NULL,
                tenant_id TEXT NOT NULL,
                user_id INTEGER,
                plan TEXT DEFAULT 'free',
                plan_expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Usage logs table (for tracking and billing)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                user_id INTEGER,
                endpoint TEXT,
                request_count INTEGER DEFAULT 1,
                cache_hits INTEGER DEFAULT 0,
                cache_misses INTEGER DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                cost_estimate REAL DEFAULT 0,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (api_key) REFERENCES api_keys (api_key),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Add user_id column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE usage_logs ADD COLUMN user_id INTEGER')
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_key ON api_keys(api_key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenant_id ON api_keys(tenant_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON api_keys(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_api_key ON usage_logs(api_key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_user_id ON usage_logs(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_tenant ON usage_logs(tenant_id)')
        
        print("Database initialized successfully")

def create_user(email: str, name: Optional[str] = None) -> int:
    """
    Create a new user.
    
    Args:
        email: User email
        name: User name (optional)
    
    Returns:
        User ID
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (email, name)
                VALUES (?, ?)
            ''', (email, name))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # User already exists, get existing user ID
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            return row['id'] if row else None

def create_api_key(
    api_key: str,
    tenant_id: str,
    user_id: Optional[int] = None,
    plan: str = 'free',
    plan_expires_at: Optional[str] = None
) -> bool:
    """
    Create a new API key record.
    
    Args:
        api_key: API key string
        tenant_id: Tenant identifier
        user_id: User ID (optional)
        plan: Plan type (default: 'free')
        plan_expires_at: Plan expiration date (optional)
    
    Returns:
        True if created successfully
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO api_keys (api_key, tenant_id, user_id, plan, plan_expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (api_key, tenant_id, user_id, plan, plan_expires_at))
            return True
        except sqlite3.IntegrityError:
            # Key already exists, update it
            # If user_id is provided and current user_id is NULL, update it
            cursor.execute('''
                UPDATE api_keys
                SET tenant_id = ?,
                    user_id = COALESCE(?, user_id),
                    plan = ?,
                    plan_expires_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE api_key = ?
            ''', (tenant_id, user_id, plan, plan_expires_at, api_key))
            return True

def get_api_key_info(api_key: str) -> Optional[Dict]:
    """
    Get API key information.
    
    Args:
        api_key: API key string
    
    Returns:
        Dictionary with key information or None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ak.*, u.email, u.name
            FROM api_keys ak
            LEFT JOIN users u ON ak.user_id = u.id
            WHERE ak.api_key = ? AND ak.is_active = 1
        ''', (api_key,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def get_tenant_plan(tenant_id: str) -> Optional[Dict]:
    """
    Get tenant's plan information.
    
    Args:
        tenant_id: Tenant identifier
    
    Returns:
        Dictionary with plan information or None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT plan, plan_expires_at, is_active, usage_count
            FROM api_keys
            WHERE tenant_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
        ''', (tenant_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def update_api_key_usage(api_key: str, tenant_id: str):
    """
    Update API key usage statistics.
    
    Args:
        api_key: API key string
        tenant_id: Tenant identifier
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE api_keys
            SET usage_count = usage_count + 1,
                last_used_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE api_key = ? AND tenant_id = ?
        ''', (api_key, tenant_id))

def log_usage(
    api_key: str,
    tenant_id: str,
    endpoint: str,
    request_count: int = 1,
    cache_hits: int = 0,
    cache_misses: int = 0,
    tokens_used: int = 0,
    cost_estimate: float = 0,
    user_id: Optional[int] = None
):
    """
    Log API usage for billing and analytics.
    
    Args:
        api_key: API key string
        tenant_id: Tenant identifier
        endpoint: API endpoint
        request_count: Number of requests
        cache_hits: Number of cache hits
        cache_misses: Number of cache misses
        tokens_used: Tokens used
        cost_estimate: Estimated cost
        user_id: User ID (optional, retrieved from api_key if not provided)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get user_id from api_key if not provided
        if user_id is None:
            key_info = get_api_key_info(api_key)
            if key_info:
                user_id = key_info.get('user_id')
        
        cursor.execute('''
            INSERT INTO usage_logs 
            (api_key, tenant_id, user_id, endpoint, request_count, cache_hits, cache_misses, tokens_used, cost_estimate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (api_key, tenant_id, user_id, endpoint, request_count, cache_hits, cache_misses, tokens_used, cost_estimate))

def get_usage_stats(tenant_id: str, days: int = 30) -> Dict:
    """
    Get usage statistics for a tenant.
    
    Args:
        tenant_id: Tenant identifier
        days: Number of days to look back
    
    Returns:
        Dictionary with usage statistics
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                SUM(request_count) as total_requests,
                SUM(cache_hits) as total_hits,
                SUM(cache_misses) as total_misses,
                SUM(tokens_used) as total_tokens,
                SUM(cost_estimate) as total_cost
            FROM usage_logs
            WHERE tenant_id = ? 
            AND logged_at >= datetime('now', '-' || ? || ' days')
        ''', (tenant_id, days))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {
            "total_requests": 0,
            "total_hits": 0,
            "total_misses": 0,
            "total_tokens": 0,
            "total_cost": 0
        }

def list_api_keys(user_id: Optional[int] = None) -> List[Dict]:
    """
    List API keys, optionally filtered by user.
    
    Args:
        user_id: User ID to filter by (optional)
    
    Returns:
        List of API key dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute('''
                SELECT ak.*, u.email, u.name
                FROM api_keys ak
                LEFT JOIN users u ON ak.user_id = u.id
                WHERE ak.user_id = ?
                ORDER BY ak.created_at DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT ak.*, u.email, u.name
                FROM api_keys ak
                LEFT JOIN users u ON ak.user_id = u.id
                ORDER BY ak.created_at DESC
            ''')
        return [dict(row) for row in cursor.fetchall()]

def deactivate_api_key(api_key: str) -> bool:
    """
    Deactivate an API key.
    
    Args:
        api_key: API key string
    
    Returns:
        True if deactivated successfully
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE api_keys
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE api_key = ?
        ''', (api_key,))
        return cursor.rowcount > 0

def update_plan(tenant_id: str, plan: str, expires_at: Optional[str] = None) -> bool:
    """
    Update tenant's plan.
    
    Args:
        tenant_id: Tenant identifier
        plan: New plan type
        expires_at: Plan expiration date (optional)
    
    Returns:
        True if updated successfully
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE api_keys
            SET plan = ?, plan_expires_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE tenant_id = ? AND is_active = 1
        ''', (plan, expires_at, tenant_id))
        return cursor.rowcount > 0

# Auth-related functions

def create_user_with_password(email: str, password_hash: str, name: Optional[str] = None, is_admin: bool = False) -> int:
    """
    Create a new user with password authentication.

    Args:
        email: User email
        password_hash: Hashed password
        name: User name (optional)
        is_admin: Whether user is an admin (default: False)

    Returns:
        User ID
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (email, password_hash, name, is_admin) VALUES (?, ?, ?, ?)',
            (email, password_hash, name, 1 if is_admin else 0)
        )
        return cursor.lastrowid

def set_user_admin(user_id: int, is_admin: bool) -> bool:
    """
    Set admin status for a user.

    Args:
        user_id: User ID
        is_admin: Admin status

    Returns:
        True if updated successfully
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET is_admin = ? WHERE id = ?',
            (1 if is_admin else 0, user_id)
        )
        return cursor.rowcount > 0

def get_user_by_email(email: str) -> Optional[Dict]:
    """
    Get user by email address.

    Args:
        email: User email

    Returns:
        User dict or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, email, name, password_hash, email_verified, is_admin, last_login_at, created_at FROM users WHERE email = ?',
            (email,)
        )
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'email': row[1],
                'name': row[2],
                'password_hash': row[3],
                'email_verified': row[4],
                'is_admin': bool(row[5]),
                'last_login_at': row[6],
                'created_at': row[7]
            }
        return None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    Get user by ID.

    Args:
        user_id: User ID

    Returns:
        User dict or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, email, name, email_verified, is_admin, last_login_at, created_at, openai_api_key_encrypted FROM users WHERE id = ?',
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'email': row[1],
                'name': row[2],
                'email_verified': row[3],
                'is_admin': bool(row[4]),
                'last_login_at': row[5],
                'created_at': row[6],
                'openai_api_key_encrypted': row[7] if len(row) > 7 else None
            }
        return None

def update_last_login(user_id: int) -> bool:
    """
    Update user's last login timestamp.

    Args:
        user_id: User ID

    Returns:
        True if updated, False otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?',
            (user_id,)
        )
        return cursor.rowcount > 0

def set_user_openai_key(user_id: int, encrypted_key: str) -> bool:
    """
    Store encrypted OpenAI API key for a user.
    
    Args:
        user_id: User ID
        encrypted_key: Encrypted OpenAI API key
    
    Returns:
        True if updated successfully
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET openai_api_key_encrypted = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (encrypted_key, user_id)
        )
        return cursor.rowcount > 0

def get_user_openai_key_encrypted(user_id: int) -> Optional[str]:
    """
    Get encrypted OpenAI API key for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        Encrypted key string or None if not set
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT openai_api_key_encrypted FROM users WHERE id = ?',
            (user_id,)
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else None

def clear_user_openai_key(user_id: int) -> bool:
    """
    Remove OpenAI API key for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        True if removed successfully
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET openai_api_key_encrypted = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (user_id,)
        )
        return cursor.rowcount > 0

# Initialize database on import
init_database()

