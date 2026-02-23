"""
Database Module - Supabase Postgres
Handles API keys, user profiles, and usage logging via Supabase Postgres.
"""
import os
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, List
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL")

_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not set. "
                "Get it from Supabase: Settings > Database > Connection string (URI)"
            )
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=DATABASE_URL
        )
    return _pool


@contextmanager
def get_db_connection():
    """Get a Postgres connection from the pool."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# ---------- Profile (User) Functions ----------

def get_user_by_id(user_id: str) -> Optional[Dict]:
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT id, email, name, is_admin, company,
                      openai_api_key_encrypted, created_at, updated_at
               FROM profiles WHERE id = %s""",
            (user_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict]:
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT id, email, name, is_admin, company,
                      openai_api_key_encrypted, created_at, updated_at
               FROM profiles WHERE email = %s""",
            (email,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def set_user_admin(user_id: str, is_admin: bool) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'UPDATE profiles SET is_admin = %s WHERE id = %s',
            (is_admin, user_id)
        )
        return cur.rowcount > 0


# ---------- OpenAI Key Functions ----------

def set_user_openai_key(user_id: str, encrypted_key: str) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'UPDATE profiles SET openai_api_key_encrypted = %s WHERE id = %s',
            (encrypted_key, user_id)
        )
        return cur.rowcount > 0


def get_user_openai_key_encrypted(user_id: str) -> Optional[str]:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT openai_api_key_encrypted FROM profiles WHERE id = %s',
            (user_id,)
        )
        row = cur.fetchone()
        return row[0] if row and row[0] else None


def clear_user_openai_key(user_id: str) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'UPDATE profiles SET openai_api_key_encrypted = NULL WHERE id = %s',
            (user_id,)
        )
        return cur.rowcount > 0


# ---------- API Key Functions ----------

def create_api_key(
    api_key: str,
    tenant_id: str,
    user_id: Optional[str] = None,
    plan: str = 'free',
    plan_expires_at: Optional[str] = None
) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO api_keys (api_key, tenant_id, user_id, plan, plan_expires_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (api_key, tenant_id, user_id, plan, plan_expires_at)
            )
            return True
        except psycopg2.IntegrityError:
            conn.rollback()
            cur.execute(
                """UPDATE api_keys
                   SET tenant_id = %s,
                       user_id = COALESCE(%s, user_id),
                       plan = %s,
                       plan_expires_at = %s,
                       updated_at = NOW()
                   WHERE api_key = %s""",
                (tenant_id, user_id, plan, plan_expires_at, api_key)
            )
            conn.commit()
            return True


def get_api_key_info(api_key: str) -> Optional[Dict]:
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT ak.*, p.email, p.name
               FROM api_keys ak
               LEFT JOIN profiles p ON ak.user_id = p.id
               WHERE ak.api_key = %s AND ak.is_active = TRUE""",
            (api_key,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_tenant_plan(tenant_id: str) -> Optional[Dict]:
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT plan, plan_expires_at, is_active, usage_count
               FROM api_keys
               WHERE tenant_id = %s AND is_active = TRUE
               ORDER BY created_at DESC LIMIT 1""",
            (tenant_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_api_key_usage(api_key: str, tenant_id: str):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """UPDATE api_keys
               SET usage_count = usage_count + 1,
                   last_used_at = NOW()
               WHERE api_key = %s AND tenant_id = %s""",
            (api_key, tenant_id)
        )


def list_api_keys(user_id: Optional[str] = None) -> List[Dict]:
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if user_id:
            cur.execute(
                """SELECT ak.*, p.email, p.name
                   FROM api_keys ak
                   LEFT JOIN profiles p ON ak.user_id = p.id
                   WHERE ak.user_id = %s
                   ORDER BY ak.created_at DESC""",
                (user_id,)
            )
        else:
            cur.execute(
                """SELECT ak.*, p.email, p.name
                   FROM api_keys ak
                   LEFT JOIN profiles p ON ak.user_id = p.id
                   ORDER BY ak.created_at DESC"""
            )
        return [dict(row) for row in cur.fetchall()]


def deactivate_api_key(api_key: str) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'UPDATE api_keys SET is_active = FALSE WHERE api_key = %s',
            (api_key,)
        )
        return cur.rowcount > 0


def update_plan(tenant_id: str, plan: str, expires_at: Optional[str] = None) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """UPDATE api_keys
               SET plan = %s, plan_expires_at = %s
               WHERE tenant_id = %s AND is_active = TRUE""",
            (plan, expires_at, tenant_id)
        )
        return cur.rowcount > 0


# ---------- Usage Logging ----------

def log_usage(
    api_key: str,
    tenant_id: str,
    endpoint: str,
    request_count: int = 1,
    cache_hits: int = 0,
    cache_misses: int = 0,
    tokens_used: int = 0,
    cost_estimate: float = 0,
    user_id: Optional[str] = None
):
    with get_db_connection() as conn:
        cur = conn.cursor()
        if user_id is None:
            key_info = get_api_key_info(api_key)
            if key_info:
                user_id = key_info.get('user_id')

        cur.execute(
            """INSERT INTO usage_logs
               (api_key, tenant_id, user_id, endpoint, request_count,
                cache_hits, cache_misses, tokens_used, cost_estimate)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (api_key, tenant_id, user_id, endpoint, request_count,
             cache_hits, cache_misses, tokens_used, cost_estimate)
        )


def get_usage_stats(tenant_id: str, days: int = 30) -> Dict:
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT
                 COALESCE(SUM(request_count), 0) as total_requests,
                 COALESCE(SUM(cache_hits), 0)    as total_hits,
                 COALESCE(SUM(cache_misses), 0)  as total_misses,
                 COALESCE(SUM(tokens_used), 0)   as total_tokens,
                 COALESCE(SUM(cost_estimate), 0)  as total_cost
               FROM usage_logs
               WHERE tenant_id = %s
                 AND logged_at >= NOW() - INTERVAL '%s days'""",
            (tenant_id, days)
        )
        row = cur.fetchone()
        return dict(row) if row else {
            "total_requests": 0, "total_hits": 0,
            "total_misses": 0, "total_tokens": 0, "total_cost": 0
        }


# ---------- Init (connection test) ----------

def init_database():
    """Test database connection on startup. Schema is managed via Supabase SQL Editor."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
        print("Database connected successfully (Supabase Postgres)")
    except Exception as e:
        print(f"WARNING: Database connection failed: {e}")
        print("Make sure DATABASE_URL is set in your .env file.")
        print("Get it from Supabase: Settings > Database > Connection string (URI)")

init_database()
