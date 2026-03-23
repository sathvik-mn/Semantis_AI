"""
Database Module - Supabase Postgres (Phase 1.1: Organization Tenancy)
Handles API keys, user profiles, organizations, audit logs, cache entries,
and usage logging via Supabase Postgres.
"""
import os
import json
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, List, Any
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
            maxconn=int(os.getenv("DB_MAX_CONNECTIONS", "25")),
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


# ==========================================================================
# Profile (User) Functions
# ==========================================================================

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


# ==========================================================================
# OpenAI Key Functions
# ==========================================================================

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


# ==========================================================================
# Organization Functions
# ==========================================================================

def create_organization(
    name: str,
    slug: str,
    owner_user_id: str,
    plan: str = 'free'
) -> Optional[Dict]:
    """Create a new organization and add the creator as owner."""
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """INSERT INTO organizations (name, slug, plan)
               VALUES (%s, %s, %s)
               RETURNING id, name, slug, plan, settings, created_at, updated_at""",
            (name, slug, plan)
        )
        org = dict(cur.fetchone())
        cur.execute(
            """INSERT INTO org_members (org_id, user_id, role)
               VALUES (%s, %s, 'owner')""",
            (org['id'], owner_user_id)
        )
        return org


def get_organization(org_id: str) -> Optional[Dict]:
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT id, name, slug, plan, settings, created_at, updated_at
               FROM organizations WHERE id = %s""",
            (org_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_org_by_slug(slug: str) -> Optional[Dict]:
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT id, name, slug, plan, settings, created_at, updated_at
               FROM organizations WHERE slug = %s""",
            (slug,)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_user_orgs(user_id: str) -> List[Dict]:
    """Return all organizations a user belongs to, with their role."""
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT o.id, o.name, o.slug, o.plan, o.settings,
                      om.role, o.created_at, o.updated_at
               FROM organizations o
               JOIN org_members om ON o.id = om.org_id
               WHERE om.user_id = %s
               ORDER BY o.created_at""",
            (user_id,)
        )
        return [dict(row) for row in cur.fetchall()]


def add_org_member(org_id: str, user_id: str, role: str = 'member') -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO org_members (org_id, user_id, role)
                   VALUES (%s, %s, %s)""",
                (org_id, user_id, role)
            )
            return True
        except psycopg2.IntegrityError:
            conn.rollback()
            return False


def remove_org_member(org_id: str, user_id: str) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM org_members WHERE org_id = %s AND user_id = %s",
            (org_id, user_id)
        )
        return cur.rowcount > 0


def update_org_settings(org_id: str, settings_dict: Dict) -> bool:
    """Merge new settings into the organization's existing JSONB settings."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """UPDATE organizations
               SET settings = settings || %s::jsonb
               WHERE id = %s""",
            (json.dumps(settings_dict), org_id)
        )
        return cur.rowcount > 0


# ==========================================================================
# API Key Functions
# ==========================================================================

def create_api_key(
    api_key: str,
    tenant_id: str,
    user_id: Optional[str] = None,
    plan: str = 'free',
    plan_expires_at: Optional[str] = None,
    org_id: Optional[str] = None,
    scope: str = 'read-write',
    label: Optional[str] = None,
    allowed_ips: Optional[List[str]] = None,
    expires_at: Optional[str] = None
) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO api_keys
                   (api_key, tenant_id, user_id, plan, plan_expires_at,
                    org_id, scope, label, allowed_ips, expires_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (api_key, tenant_id, user_id, plan, plan_expires_at,
                 org_id, scope, label, allowed_ips, expires_at)
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
                       org_id = COALESCE(%s, org_id),
                       scope = %s,
                       label = COALESCE(%s, label),
                       allowed_ips = COALESCE(%s, allowed_ips),
                       expires_at = COALESCE(%s, expires_at),
                       updated_at = NOW()
                   WHERE api_key = %s""",
                (tenant_id, user_id, plan, plan_expires_at,
                 org_id, scope, label, allowed_ips, expires_at, api_key)
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


def get_org_for_api_key(api_key: str) -> Optional[Dict]:
    """Return the organization associated with an API key."""
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT o.id, o.name, o.slug, o.plan, o.settings
               FROM api_keys ak
               JOIN organizations o ON ak.org_id = o.id
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


# ==========================================================================
# Usage Logging
# ==========================================================================

def log_usage(
    api_key: str,
    tenant_id: str,
    endpoint: str,
    request_count: int = 1,
    cache_hits: int = 0,
    cache_misses: int = 0,
    tokens_used: int = 0,
    cost_estimate: float = 0,
    user_id: Optional[str] = None,
    org_id: Optional[str] = None
):
    with get_db_connection() as conn:
        cur = conn.cursor()
        if user_id is None or org_id is None:
            key_info = get_api_key_info(api_key)
            if key_info:
                user_id = user_id or key_info.get('user_id')
                org_id = org_id or key_info.get('org_id')

        cur.execute(
            """INSERT INTO usage_logs
               (api_key, tenant_id, user_id, org_id, endpoint, request_count,
                cache_hits, cache_misses, tokens_used, cost_estimate)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (api_key, tenant_id, user_id, org_id, endpoint, request_count,
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
                 AND logged_at >= NOW() - INTERVAL '1 day' * %s""",
            (tenant_id, days)
        )
        row = cur.fetchone()
        result = dict(row) if row else {
            "total_requests": 0, "total_hits": 0,
            "total_misses": 0, "total_tokens": 0, "total_cost": 0
        }
        # Fallback to api_keys.usage_count if usage_logs is empty
        if result.get('total_requests', 0) == 0:
            cur.execute("""
                SELECT COALESCE(SUM(usage_count), 0) as total_requests
                FROM api_keys
                WHERE tenant_id = %s AND is_active = TRUE
            """, (tenant_id,))
            fallback = cur.fetchone()
            if fallback and (fallback['total_requests'] or 0) > 0:
                result['total_requests'] = fallback['total_requests']
        return result


def get_usage_stats_by_org(org_id: str, days: int = 30) -> Dict:
    """Get usage stats aggregated by org_id (for billing/savings)."""
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
               WHERE org_id = %s
                 AND logged_at >= NOW() - INTERVAL '1 day' * %s""",
            (org_id, days)
        )
        row = cur.fetchone()
        result = dict(row) if row else {
            "total_requests": 0, "total_hits": 0,
            "total_misses": 0, "total_tokens": 0, "total_cost": 0
        }
        if result.get('total_requests', 0) > 0:
            return result
        # Fallback: sum by tenant_id for API keys belonging to this org
        cur.execute(
            """SELECT
                 COALESCE(SUM(ul.request_count), 0) as total_requests,
                 COALESCE(SUM(ul.cache_hits), 0)    as total_hits,
                 COALESCE(SUM(ul.cache_misses), 0)  as total_misses,
                 COALESCE(SUM(ul.tokens_used), 0)   as total_tokens,
                 COALESCE(SUM(ul.cost_estimate), 0)  as total_cost
               FROM usage_logs ul
               JOIN api_keys ak ON ul.api_key = ak.api_key AND ak.org_id = %s
               WHERE ul.logged_at >= NOW() - INTERVAL '1 day' * %s""",
            (org_id, days)
        )
        row = cur.fetchone()
        result = dict(row) if row else {
            "total_requests": 0, "total_hits": 0,
            "total_misses": 0, "total_tokens": 0, "total_cost": 0
        }
        # Fallback to api_keys.usage_count if usage_logs is empty
        if result.get('total_requests', 0) == 0:
            cur.execute("""
                SELECT
                    COALESCE(SUM(usage_count), 0) as total_requests,
                    MAX(last_used_at) as last_used
                FROM api_keys
                WHERE org_id = %s AND is_active = TRUE
            """, (org_id,))
            fallback = cur.fetchone()
            if fallback and (fallback['total_requests'] or 0) > 0:
                result['total_requests'] = fallback['total_requests']
        return result


# ==========================================================================
# Audit Logging
# ==========================================================================

def log_audit(
    org_id: Optional[str],
    user_id: Optional[str],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO audit_logs
               (org_id, user_id, action, resource_type, resource_id, details, ip_address)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (org_id, user_id, action, resource_type, resource_id,
             json.dumps(details) if details else '{}', ip_address)
        )
        return True


# ==========================================================================
# Cache Entries
# ==========================================================================

def store_cache_entry(
    org_id: str,
    prompt_hash: str,
    prompt_norm: str,
    response_text: str,
    embedding_bytes: Optional[bytes] = None,
    model: str = 'gpt-4o-mini',
    ttl_expires_at: Optional[str] = None,
    domain: str = 'general',
    tenant_id: str = ''
) -> Optional[Dict]:
    """Insert or update a cache entry. Encrypts prompt and response if configured."""
    from encryption import encrypt_cache_entry, is_cache_encryption_enabled
    # Encrypt sensitive fields if enabled
    stored_prompt = encrypt_cache_entry(prompt_norm, tenant_id) if tenant_id else prompt_norm
    stored_response = encrypt_cache_entry(response_text, tenant_id) if tenant_id else response_text
    is_encrypted = is_cache_encryption_enabled() and bool(tenant_id)

    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """INSERT INTO cache_entries
               (org_id, prompt_hash, prompt_norm, response_text, embedding,
                model, ttl_expires_at, domain, is_encrypted)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (id) DO NOTHING
               RETURNING id, org_id, prompt_hash, model, created_at""",
            (org_id, prompt_hash, stored_prompt, stored_response,
             embedding_bytes, model, ttl_expires_at, domain, is_encrypted)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_cache_entry(org_id: str, prompt_hash: str, tenant_id: str = '') -> Optional[Dict]:
    """Retrieve a cache entry, decrypt if encrypted, and bump use_count."""
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT id, org_id, prompt_hash, prompt_norm, response_text,
                      model, ttl_expires_at, created_at, last_used_at, use_count, domain,
                      COALESCE(is_encrypted, FALSE) as is_encrypted
               FROM cache_entries
               WHERE org_id = %s AND prompt_hash = %s
                 AND (ttl_expires_at IS NULL OR ttl_expires_at > NOW())
               ORDER BY created_at DESC
               LIMIT 1""",
            (org_id, prompt_hash)
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                """UPDATE cache_entries
                   SET use_count = use_count + 1, last_used_at = NOW()
                   WHERE id = %s""",
                (row['id'],)
            )
            result = dict(row)
            # Decrypt if encrypted
            if result.get('is_encrypted') and tenant_id:
                from encryption import decrypt_cache_entry
                result['prompt_norm'] = decrypt_cache_entry(result['prompt_norm'], tenant_id)
                result['response_text'] = decrypt_cache_entry(result['response_text'], tenant_id)
            return result
        return None


def list_cache_entries(
    org_id: str, limit: int = 100, offset: int = 0,
    search: Optional[str] = None, tenant_id: str = '',
) -> List[Dict]:
    """List cache entries with optional search and pagination."""
    with get_db_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if search:
            cur.execute(
                """SELECT id, org_id, prompt_hash, prompt_norm, response_text,
                          model, ttl_expires_at, created_at, last_used_at, use_count, domain,
                          COALESCE(is_encrypted, FALSE) as is_encrypted
                   FROM cache_entries
                   WHERE org_id = %s AND prompt_norm ILIKE %s
                   ORDER BY last_used_at DESC NULLS LAST
                   LIMIT %s OFFSET %s""",
                (org_id, f"%{search}%", limit, offset)
            )
        else:
            cur.execute(
                """SELECT id, org_id, prompt_hash, prompt_norm, response_text,
                          model, ttl_expires_at, created_at, last_used_at, use_count, domain,
                          COALESCE(is_encrypted, FALSE) as is_encrypted
                   FROM cache_entries
                   WHERE org_id = %s
                   ORDER BY last_used_at DESC NULLS LAST
                   LIMIT %s OFFSET %s""",
                (org_id, limit, offset)
            )
        rows = [dict(row) for row in cur.fetchall()]
        if tenant_id:
            from encryption import decrypt_cache_entry
            for row in rows:
                if row.get('is_encrypted'):
                    row['prompt_norm'] = decrypt_cache_entry(row['prompt_norm'], tenant_id)
                    row['response_text'] = decrypt_cache_entry(row['response_text'], tenant_id)
        return rows


def count_cache_entries(org_id: str, search: Optional[str] = None) -> int:
    """Count total cache entries for pagination."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        if search:
            cur.execute(
                "SELECT COUNT(*) FROM cache_entries WHERE org_id = %s AND prompt_norm ILIKE %s",
                (org_id, f"%{search}%")
            )
        else:
            cur.execute(
                "SELECT COUNT(*) FROM cache_entries WHERE org_id = %s",
                (org_id,)
            )
        return cur.fetchone()[0]


def delete_cache_entry(entry_id: int, org_id: str) -> bool:
    """Delete a cache entry by ID, scoped to org for security."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM cache_entries WHERE id = %s AND org_id = %s",
            (entry_id, org_id)
        )
        return cur.rowcount > 0


def delete_cache_entries_bulk(entry_ids: List[int], org_id: str) -> int:
    """Delete multiple cache entries, scoped to org. Returns count deleted."""
    if not entry_ids:
        return 0
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM cache_entries WHERE id = ANY(%s) AND org_id = %s",
            (entry_ids, org_id)
        )
        return cur.rowcount


# ==========================================================================
# Init (connection test)
# ==========================================================================

import logging

_db_log = logging.getLogger("database")


# ==========================================================================
# Data Retention / Cleanup
# ==========================================================================

def cleanup_old_logs(usage_days: int = 90, audit_days: int = 365) -> dict:
    """Delete usage_logs older than `usage_days` and audit_logs older than `audit_days`.

    Returns dict with counts of deleted rows.  Safe to call from a cron job
    or a scheduled background thread.
    """
    result = {"usage_deleted": 0, "audit_deleted": 0}
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM usage_logs WHERE logged_at < NOW() - INTERVAL '1 day' * %s",
                (usage_days,)
            )
            result["usage_deleted"] = cur.rowcount
            cur.execute(
                "DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '1 day' * %s",
                (audit_days,)
            )
            result["audit_deleted"] = cur.rowcount
        _db_log.info(
            f"Log cleanup: deleted {result['usage_deleted']} usage rows (>{usage_days}d), "
            f"{result['audit_deleted']} audit rows (>{audit_days}d)"
        )
    except Exception as e:
        _db_log.warning(f"Log cleanup failed: {e}")
    return result


# ==========================================================================
# Init (connection test)
# ==========================================================================

def init_database():
    """Test database connection on startup. Schema is managed via Supabase SQL Editor."""
    if not DATABASE_URL:
        _db_log.warning(
            "DATABASE_URL is not set. Database features will be unavailable. "
            "Get it from Supabase: Settings > Database > Connection string (URI)"
        )
        return
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
        _db_log.info("Database connected successfully (Supabase Postgres)")
    except Exception as e:
        _db_log.warning(
            f"Database connection failed: {e}. "
            "Cache and semantic matching will still work without the database. "
            "Auth, API key management, and billing require a database connection."
        )

init_database()
