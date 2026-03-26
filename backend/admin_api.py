"""
Admin API Endpoints for Dashboard
Provides comprehensive analytics, user management, and business insights.
Uses Supabase Postgres via psycopg2.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from typing import Optional
from pydantic import BaseModel
import os
from psycopg2.extras import RealDictCursor
from database import (
    get_db_connection, get_usage_stats,
    update_plan, deactivate_api_key
)
import logging

def get_logger(name):
    return logging.getLogger(name)

system_log = get_logger("system")
app_log = get_logger("application")
error_log = get_logger("errors")

def get_svc():
    from semantic_cache_server import svc
    return svc

admin_router = APIRouter(prefix="/admin", tags=["admin"])

# ── Admin rate limiting ──
# Track admin requests per IP with a simple in-memory counter.
# Allows 60 requests per minute per IP across all admin endpoints.
_admin_rate_limit: dict = {}  # {ip: [timestamps]}
_ADMIN_RATE_LIMIT = 60  # requests per minute
_ADMIN_RATE_WINDOW = 60  # seconds

import time as _time

def _check_admin_rate_limit(request: Request):
    """Rate limit all admin endpoints to prevent abuse."""
    ip = request.client.host if request.client else "unknown"
    now = _time.time()
    # Clean old entries
    if ip in _admin_rate_limit:
        _admin_rate_limit[ip] = [t for t in _admin_rate_limit[ip] if now - t < _ADMIN_RATE_WINDOW]
    else:
        _admin_rate_limit[ip] = []
    if len(_admin_rate_limit[ip]) >= _ADMIN_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Admin rate limit exceeded. Try again in a minute.")
    _admin_rate_limit[ip].append(now)
    # Evict stale IPs periodically (keep dict small)
    if len(_admin_rate_limit) > 1000:
        cutoff = now - _ADMIN_RATE_WINDOW
        _admin_rate_limit.clear()

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

if not ADMIN_API_KEY:
    system_log.warning("ADMIN_API_KEY is not set. Admin endpoints are disabled.")


def verify_admin_key(
    x_admin_key: str = Header(None, alias="X-Admin-Key"),
    api_key: str = Query(None),
    authorization: str = Header(None),
):
    import hmac

    # Method 1: Admin API key (server-to-server calls)
    key = x_admin_key or api_key
    if ADMIN_API_KEY and key and hmac.compare_digest(key, ADMIN_API_KEY):
        return True

    # Method 2: Supabase JWT with is_admin=true (browser-based admin panel)
    if authorization and authorization.startswith("Bearer "):
        try:
            from auth import verify_token
            from database import get_user_by_id
            token = authorization.split(" ", 1)[1]
            payload = verify_token(token)
            user_id = payload.get("sub")
            if user_id:
                user = get_user_by_id(user_id)
                if user and user.get("is_admin"):
                    return True
        except Exception:
            pass

    if not ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Admin API is not configured. Set ADMIN_API_KEY env var.")
    raise HTTPException(status_code=401, detail="Admin access required. Provide a valid admin API key or sign in as an admin user.")

def require_admin(request: Request, admin_verified: bool = Depends(verify_admin_key)):
    _check_admin_rate_limit(request)
    return admin_verified


class AnalyticsSummary(BaseModel):
    total_users: int
    total_api_keys: int
    active_users: int
    total_requests: int
    total_cache_hits: int
    total_cache_misses: int
    cache_hit_ratio: float
    total_tokens_used: int
    total_cost_estimate: float


@admin_router.get("/analytics/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    admin: bool = Depends(require_admin)
):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("SELECT COUNT(DISTINCT id) as count FROM profiles")
            total_users = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM api_keys")
            total_api_keys = cur.fetchone()['count']

            cur.execute("""
                SELECT COUNT(DISTINCT tenant_id) as count
                FROM api_keys
                WHERE is_active = TRUE
                  AND (last_used_at >= NOW() - INTERVAL '1 day' * %s OR last_used_at IS NULL)
            """, (days,))
            active_users = cur.fetchone()['count']

            cur.execute("""
                SELECT
                    COALESCE(SUM(request_count), 0) as total_requests,
                    COALESCE(SUM(cache_hits), 0) as total_hits,
                    COALESCE(SUM(cache_misses), 0) as total_misses,
                    COALESCE(SUM(tokens_used), 0) as total_tokens,
                    COALESCE(SUM(cost_estimate), 0) as total_cost
                FROM usage_logs
                WHERE logged_at >= NOW() - INTERVAL '1 day' * %s
            """, (days,))
            usage = cur.fetchone()

            total_requests = usage['total_requests'] or 0
            total_hits = usage['total_hits'] or 0
            total_cost = usage['total_cost'] or 0
            hit_ratio = (total_hits / total_requests * 100) if total_requests > 0 else 0.0

            return AnalyticsSummary(
                total_users=total_users,
                total_api_keys=total_api_keys,
                active_users=active_users,
                total_requests=total_requests,
                total_cache_hits=total_hits,
                total_cache_misses=usage['total_misses'] or 0,
                cache_hit_ratio=round(hit_ratio, 2),
                total_tokens_used=usage['total_tokens'] or 0,
                total_cost_estimate=round(total_cost, 2)
            )
    except Exception as e:
        error_log.exception(f"Admin analytics summary failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/analytics/user-growth")
def get_user_growth(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=1, le=365),
    admin: bool = Depends(require_admin)
):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            if period == "daily":
                date_expr = "DATE(created_at)"
            elif period == "weekly":
                date_expr = "TO_CHAR(created_at, 'IYYY-\"W\"IW')"
            else:
                date_expr = "TO_CHAR(created_at, 'YYYY-MM')"

            cur.execute(f"""
                SELECT {date_expr} as period, COUNT(*) as new_users
                FROM profiles
                WHERE created_at >= NOW() - INTERVAL '1 day' * %s
                GROUP BY {date_expr}
                ORDER BY period ASC
            """, (days,))
            user_growth = [dict(row) for row in cur.fetchall()]

            if period == "daily":
                date_expr_k = "DATE(created_at)"
            elif period == "weekly":
                date_expr_k = "TO_CHAR(created_at, 'IYYY-\"W\"IW')"
            else:
                date_expr_k = "TO_CHAR(created_at, 'YYYY-MM')"

            cur.execute(f"""
                SELECT {date_expr_k} as period, COUNT(DISTINCT tenant_id) as new_keys
                FROM api_keys
                WHERE created_at >= NOW() - INTERVAL '1 day' * %s
                GROUP BY {date_expr_k}
                ORDER BY period ASC
            """, (days,))
            key_growth = {str(row['period']): row['new_keys'] for row in cur.fetchall()}

            result = []
            for row in user_growth:
                p = str(row['period'])
                result.append({
                    "date": p,
                    "new_users": row['new_users'],
                    "new_api_keys": key_growth.get(p, 0),
                    "total_users": sum(r['new_users'] for r in user_growth if str(r['period']) <= p)
                })

            return {"period": period, "days": days, "data": result}
    except Exception as e:
        error_log.exception(f"Admin user growth failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/analytics/plan-distribution")
def get_plan_distribution(admin: bool = Depends(require_admin)):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Use organization plan (Stripe-verified) as source of truth
            cur.execute("""
                SELECT
                    COALESCE(o.plan, 'free') as plan,
                    COUNT(DISTINCT p.id) as count,
                    COALESCE(SUM(ul.request_count), 0) as total_requests,
                    COALESCE(SUM(ul.tokens_used), 0) as total_tokens,
                    COALESCE(SUM(ul.cost_estimate), 0) as total_cost
                FROM profiles p
                LEFT JOIN org_members om ON p.id = om.user_id
                LEFT JOIN organizations o ON om.org_id = o.id
                LEFT JOIN api_keys ak ON p.id = ak.user_id AND ak.is_active = TRUE
                LEFT JOIN usage_logs ul ON ak.api_key = ul.api_key
                GROUP BY o.plan
            """)
            plans = [dict(row) for row in cur.fetchall()]
            total_users = sum(p['count'] for p in plans)

            result = []
            for plan in plans:
                pct = (plan['count'] / total_users * 100) if total_users > 0 else 0
                result.append({
                    "plan": plan['plan'] or 'free',
                    "count": plan['count'],
                    "percentage": round(pct, 2),
                    "total_requests": plan['total_requests'] or 0,
                    "total_tokens": plan['total_tokens'] or 0,
                    "total_cost": round(plan['total_cost'] or 0, 2)
                })

            return {"total_active_keys": total_users, "plans": result}
    except Exception as e:
        error_log.exception(f"Admin plan distribution failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/analytics/usage-trends")
def get_usage_trends(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=1, le=365),
    admin: bool = Depends(require_admin)
):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            if period == "daily":
                date_expr = "DATE(logged_at)"
            elif period == "weekly":
                date_expr = "TO_CHAR(logged_at, 'IYYY-\"W\"IW')"
            else:
                date_expr = "TO_CHAR(logged_at, 'YYYY-MM')"

            cur.execute(f"""
                SELECT
                    {date_expr} as period,
                    COALESCE(SUM(request_count), 0) as requests,
                    COALESCE(SUM(cache_hits), 0) as hits,
                    COALESCE(SUM(cache_misses), 0) as misses,
                    COALESCE(SUM(tokens_used), 0) as tokens,
                    COALESCE(SUM(cost_estimate), 0) as cost
                FROM usage_logs
                WHERE logged_at >= NOW() - INTERVAL '1 day' * %s
                GROUP BY {date_expr}
                ORDER BY period ASC
            """, (days,))

            trends = []
            for row in cur.fetchall():
                d = dict(row)
                total_reqs = d['requests'] or 0
                hits = d['hits'] or 0
                hit_ratio = (hits / total_reqs * 100) if total_reqs > 0 else 0
                trends.append({
                    "date": str(d['period']),
                    "requests": total_reqs,
                    "cache_hits": hits,
                    "cache_misses": d['misses'] or 0,
                    "cache_hit_ratio": round(hit_ratio, 2),
                    "tokens_used": d['tokens'] or 0,
                    "cost_estimate": round(d['cost'] or 0, 2)
                })

            return {"period": period, "days": days, "data": trends}
    except Exception as e:
        error_log.exception(f"Admin usage trends failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/analytics/top-users")
def get_top_users(
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("usage_count", regex="^(usage_count|requests|cost|tokens)$"),
    days: int = Query(30, ge=1, le=365),
    admin: bool = Depends(require_admin)
):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            if sort_by == "tokens":
                order_by = "total_tokens DESC"
            elif sort_by == "requests":
                order_by = "total_requests DESC"
            elif sort_by == "cost":
                order_by = "total_cost DESC"
            else:
                order_by = "total_requests DESC"

            # Aggregate by user (p.id) not by API key to avoid duplicates
            cur.execute(f"""
                SELECT
                    p.id as user_id, p.email, p.name,
                    COALESCE(o.plan, 'free') as plan,
                    MIN(ak.created_at) as created_at,
                    MAX(ak.last_used_at) as last_used_at,
                    COALESCE(SUM(ul.request_count), 0) as total_requests,
                    COALESCE(SUM(ul.cache_hits), 0) as total_hits,
                    COALESCE(SUM(ul.cache_misses), 0) as total_misses,
                    COALESCE(SUM(ul.tokens_used), 0) as total_tokens,
                    COALESCE(SUM(ul.cost_estimate), 0) as total_cost
                FROM profiles p
                JOIN api_keys ak ON p.id = ak.user_id AND ak.is_active = TRUE
                LEFT JOIN usage_logs ul ON ak.api_key = ul.api_key
                    AND ul.logged_at >= NOW() - INTERVAL '1 day' * %s
                LEFT JOIN org_members om ON p.id = om.user_id
                LEFT JOIN organizations o ON om.org_id = o.id
                GROUP BY p.id, p.email, p.name, o.plan
                ORDER BY {order_by}
                LIMIT %s
            """, (days, limit))

            users = []
            for row in cur.fetchall():
                d = dict(row)
                total_reqs = d['total_requests'] or 0
                hits = d['total_hits'] or 0
                tokens = d['total_tokens'] or 0
                hit_ratio = (hits / total_reqs * 100) if total_reqs > 0 else 0
                users.append({
                    "user_id": str(d['user_id']),
                    "email": d['email'],
                    "name": d['name'],
                    "plan": d['plan'] or 'free',
                    "created_at": str(d['created_at']),
                    "last_used_at": str(d['last_used_at']) if d['last_used_at'] else None,
                    "total_requests": total_reqs,
                    "total_cache_hits": hits,
                    "total_cache_misses": d['total_misses'] or 0,
                    "cache_hit_ratio": round(hit_ratio, 2),
                    "total_tokens": tokens,
                    "total_cost": round(d['total_cost'] or 0, 4)
                })

            return {"limit": limit, "sort_by": sort_by, "days": days, "users": users}
    except Exception as e:
        error_log.exception(f"Admin top users failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/users")
def list_all_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    admin: bool = Depends(require_admin)
):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            base_query = """
                    SELECT
                        p.id, p.email, p.name, p.created_at, p.updated_at,
                        COUNT(DISTINCT ak.id) as api_key_count,
                        MAX(ak.last_used_at) as last_used_at,
                        COALESCE(o.plan, 'free') as org_plan,
                        COALESCE(SUM(ul.request_count), 0) as total_requests,
                        COALESCE(SUM(ul.cache_hits), 0) as total_cache_hits,
                        COALESCE(SUM(ul.cache_misses), 0) as total_cache_misses,
                        COALESCE(SUM(ul.tokens_used), 0) as total_tokens,
                        COALESCE(SUM(ul.cost_estimate), 0) as total_cost
                    FROM profiles p
                    LEFT JOIN api_keys ak ON p.id = ak.user_id
                    LEFT JOIN usage_logs ul ON ak.api_key = ul.api_key
                    LEFT JOIN org_members om ON p.id = om.user_id
                    LEFT JOIN organizations o ON om.org_id = o.id
            """
            if search:
                cur.execute(base_query + """
                    WHERE p.email ILIKE %s OR p.name ILIKE %s
                    GROUP BY p.id, o.plan
                    ORDER BY p.created_at DESC
                    LIMIT %s OFFSET %s
                """, (f"%{search}%", f"%{search}%", limit, offset))
            else:
                cur.execute(base_query + """
                    GROUP BY p.id, o.plan
                    ORDER BY p.created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))

            users = []
            for row in cur.fetchall():
                d = dict(row)
                users.append({
                    "id": str(d['id']),
                    "email": d['email'],
                    "name": d['name'],
                    "created_at": str(d['created_at']),
                    "updated_at": str(d['updated_at']) if d['updated_at'] else None,
                    "api_key_count": d['api_key_count'] or 0,
                    "total_usage": d['total_requests'] or 0,
                    "total_requests": d['total_requests'] or 0,
                    "total_cache_hits": d['total_cache_hits'] or 0,
                    "total_cache_misses": d['total_cache_misses'] or 0,
                    "total_tokens": d['total_tokens'] or 0,
                    "total_cost": round(d['total_cost'] or 0, 4),
                    "plan": d['org_plan'] or 'free',
                    "last_used_at": str(d['last_used_at']) if d['last_used_at'] else None
                })

            if search:
                cur.execute(
                    "SELECT COUNT(*) as count FROM profiles WHERE email ILIKE %s OR name ILIKE %s",
                    (f"%{search}%", f"%{search}%")
                )
            else:
                cur.execute("SELECT COUNT(*) as count FROM profiles")

            total = cur.fetchone()['count']

            return {"total": total, "limit": limit, "offset": offset, "users": users}
    except Exception as e:
        error_log.exception(f"Admin list users failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/users/by-uid/{user_id}/details")
def get_user_details_by_uid(user_id: str, admin: bool = Depends(require_admin)):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get profile
            cur.execute("SELECT id, email, name, is_admin, company, created_at, updated_at FROM profiles WHERE id = %s", (user_id,))
            profile = cur.fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail="User not found")
            profile = dict(profile)

            # Get all API keys for this user
            cur.execute("""
                SELECT id, api_key, tenant_id, plan, is_active, scope, label,
                       usage_count, created_at, last_used_at, expires_at
                FROM api_keys WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            api_keys = []
            for row in cur.fetchall():
                d = dict(row)
                d['api_key'] = d['api_key'][:12] + "..." + d['api_key'][-4:] if len(d['api_key']) > 16 else d['api_key']
                d['created_at'] = str(d['created_at'])
                d['last_used_at'] = str(d['last_used_at']) if d['last_used_at'] else None
                d['expires_at'] = str(d['expires_at']) if d['expires_at'] else None
                api_keys.append(d)

            # Get org memberships
            cur.execute("""
                SELECT o.id as org_id, o.name as org_name, o.slug, o.plan as org_plan, om.role
                FROM org_members om
                JOIN organizations o ON om.org_id = o.id
                WHERE om.user_id = %s
            """, (user_id,))
            orgs = [dict(row) for row in cur.fetchall()]
            for org in orgs:
                org['org_id'] = str(org['org_id'])

            # Get usage stats (30d) aggregated across all user's keys
            cur.execute("""
                SELECT
                    COALESCE(SUM(ul.request_count), 0) as total_requests,
                    COALESCE(SUM(ul.cache_hits), 0) as total_hits,
                    COALESCE(SUM(ul.cache_misses), 0) as total_misses,
                    COALESCE(SUM(ul.tokens_used), 0) as total_tokens,
                    COALESCE(SUM(ul.cost_estimate), 0) as total_cost
                FROM usage_logs ul
                JOIN api_keys ak ON ul.api_key = ak.api_key
                WHERE ak.user_id = %s AND ul.logged_at >= NOW() - INTERVAL '30 days'
            """, (user_id,))
            usage_30d = dict(cur.fetchone())

            # Get recent activity by endpoint (7d)
            cur.execute("""
                SELECT
                    ul.endpoint,
                    COALESCE(SUM(ul.request_count), 0) as requests,
                    COALESCE(SUM(ul.cache_hits), 0) as hits,
                    COALESCE(SUM(ul.cache_misses), 0) as misses,
                    COALESCE(SUM(ul.cost_estimate), 0) as cost
                FROM usage_logs ul
                JOIN api_keys ak ON ul.api_key = ak.api_key
                WHERE ak.user_id = %s AND ul.logged_at >= NOW() - INTERVAL '7 days'
                GROUP BY ul.endpoint
            """, (user_id,))
            recent_activity = [dict(row) for row in cur.fetchall()]
            for a in recent_activity:
                a['cost'] = round(a['cost'] or 0, 4)

            # Get recent audit logs for user's orgs
            org_ids = [org['org_id'] for org in orgs]
            audit_logs = []
            if org_ids:
                placeholders = ','.join(['%s'] * len(org_ids))
                cur.execute(f"""
                    SELECT id, action, resource_type, resource_id, details, created_at
                    FROM audit_logs
                    WHERE user_id = %s OR org_id IN ({placeholders})
                    ORDER BY created_at DESC
                    LIMIT 10
                """, (user_id, *org_ids))
                audit_logs = [dict(row) for row in cur.fetchall()]
                for log in audit_logs:
                    log['created_at'] = str(log['created_at'])
                    log['details'] = log['details'] or {}

            return {
                "id": str(profile['id']),
                "email": profile['email'],
                "name": profile['name'],
                "is_admin": profile['is_admin'],
                "company": profile['company'],
                "created_at": str(profile['created_at']),
                "updated_at": str(profile['updated_at']) if profile['updated_at'] else None,
                "api_keys": api_keys,
                "organizations": orgs,
                "usage_stats_30d": {
                    "total_requests": usage_30d['total_requests'] or 0,
                    "total_hits": usage_30d['total_hits'] or 0,
                    "total_misses": usage_30d['total_misses'] or 0,
                    "total_tokens": usage_30d['total_tokens'] or 0,
                    "total_cost": round(usage_30d['total_cost'] or 0, 4),
                },
                "recent_activity": recent_activity,
                "audit_logs": audit_logs,
            }
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Admin user details by uid failed | user={user_id} | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.post("/users/by-uid/{user_id}/update-plan")
def update_user_plan_by_uid(
    user_id: str,
    plan: str = Query(...),
    admin: bool = Depends(require_admin)
):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            # Update api_keys plan
            cur.execute("UPDATE api_keys SET plan = %s WHERE user_id = %s RETURNING id", (plan, user_id))
            rows = cur.fetchall()
            if not rows:
                raise HTTPException(status_code=404, detail="No API keys found for user")
            # Also update organization plan (source of truth for billing)
            cur.execute("""
                UPDATE organizations SET plan = %s
                WHERE id IN (
                    SELECT org_id FROM org_members WHERE user_id = %s
                )
            """, (plan, user_id))
            return {"success": True, "message": f"Plan updated to {plan} for {len(rows)} key(s)", "updated_count": len(rows)}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Admin plan update by uid failed | user={user_id} | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.post("/users/by-uid/{user_id}/deactivate")
def deactivate_user_by_uid(user_id: str, admin: bool = Depends(require_admin)):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("UPDATE api_keys SET is_active = FALSE WHERE user_id = %s RETURNING id", (user_id,))
            rows = cur.fetchall()
            if not rows:
                raise HTTPException(status_code=404, detail="No API keys found for user")
            return {"success": True, "message": f"Deactivated {len(rows)} key(s)", "updated_count": len(rows)}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Admin deactivate by uid failed | user={user_id} | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.post("/users/by-uid/{user_id}/activate")
def activate_user_by_uid(user_id: str, admin: bool = Depends(require_admin)):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("UPDATE api_keys SET is_active = TRUE WHERE user_id = %s RETURNING id", (user_id,))
            rows = cur.fetchall()
            if not rows:
                raise HTTPException(status_code=404, detail="No API keys found for user")
            return {"success": True, "message": f"Activated {len(rows)} key(s)", "updated_count": len(rows)}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Admin activate by uid failed | user={user_id} | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/users/{tenant_id}/details")
def get_user_details(tenant_id: str, admin: bool = Depends(require_admin)):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT ak.*, p.email, p.name
                FROM api_keys ak
                LEFT JOIN profiles p ON ak.user_id = p.id
                WHERE ak.tenant_id = %s
                ORDER BY ak.created_at DESC
                LIMIT 1
            """, (tenant_id,))

            key_info = cur.fetchone()
            if not key_info:
                raise HTTPException(status_code=404, detail="Tenant not found")
            d = dict(key_info)

            usage_stats = get_usage_stats(tenant_id, days=30)

            cache_stats = {}
            try:
                cache_stats = get_svc().metrics(tenant_id)
            except Exception:
                pass

            cur.execute("""
                SELECT
                    endpoint,
                    COALESCE(SUM(request_count), 0) as requests,
                    COALESCE(SUM(cache_hits), 0) as hits,
                    COALESCE(SUM(cache_misses), 0) as misses,
                    COALESCE(SUM(tokens_used), 0) as tokens,
                    COALESCE(SUM(cost_estimate), 0) as cost
                FROM usage_logs
                WHERE tenant_id = %s AND logged_at >= NOW() - INTERVAL '7 days'
                GROUP BY endpoint
            """, (tenant_id,))
            recent_activity = [dict(row) for row in cur.fetchall()]

            return {
                "tenant_id": tenant_id,
                "api_key": d['api_key'][:20] + "..." if len(d['api_key']) > 20 else d['api_key'],
                "email": d['email'],
                "name": d['name'],
                "plan": d['plan'],
                "plan_expires_at": str(d['plan_expires_at']) if d['plan_expires_at'] else None,
                "is_active": bool(d['is_active']),
                "created_at": str(d['created_at']),
                "last_used_at": str(d['last_used_at']) if d['last_used_at'] else None,
                "usage_count": d['usage_count'],
                "usage_stats_30d": usage_stats,
                "cache_stats": cache_stats,
                "recent_activity": recent_activity
            }
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Admin user details failed | tenant={tenant_id} | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.post("/users/{tenant_id}/update-plan")
def update_user_plan(
    tenant_id: str,
    plan: str = Query(...),
    expires_at: Optional[str] = Query(None),
    admin: bool = Depends(require_admin)
):
    try:
        success = update_plan(tenant_id, plan, expires_at)
        if success:
            return {"success": True, "message": f"Plan updated to {plan} for tenant {tenant_id}"}
        raise HTTPException(status_code=404, detail="Tenant not found")
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Admin plan update failed | tenant={tenant_id} | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.post("/users/{tenant_id}/deactivate")
def deactivate_user(tenant_id: str, admin: bool = Depends(require_admin)):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT api_key FROM api_keys WHERE tenant_id = %s", (tenant_id,))
            key_row = cur.fetchone()
            if not key_row:
                raise HTTPException(status_code=404, detail="Tenant not found")
            success = deactivate_api_key(key_row['api_key'])
            if success:
                return {"success": True, "message": f"API key deactivated for tenant {tenant_id}"}
            raise HTTPException(status_code=500, detail="Failed to deactivate")
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Admin deactivate user failed | tenant={tenant_id} | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/system/stats")
def get_system_stats(admin: bool = Depends(require_admin)):
    try:
        svc_instance = get_svc()
        total_tenants = len(svc_instance.tenants)
        total_entries = sum(len(t.rows) for t in svc_instance.tenants.values())

        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("SELECT COUNT(*) as count FROM profiles")
            total_users = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM api_keys WHERE is_active = TRUE")
            active_keys = cur.fetchone()['count']

            cur.execute("""
                SELECT
                    COALESCE(SUM(request_count), 0) as total_requests,
                    COALESCE(SUM(cache_hits), 0) as total_hits,
                    COALESCE(SUM(cache_misses), 0) as total_misses
                FROM usage_logs
                WHERE logged_at >= NOW() - INTERVAL '24 hours'
            """)
            daily_stats = cur.fetchone()

        return {
            "cache": {
                "total_tenants": total_tenants,
                "total_cache_entries": total_entries,
                "avg_entries_per_tenant": round(total_entries / total_tenants, 2) if total_tenants > 0 else 0
            },
            "database": {
                "total_users": total_users,
                "active_api_keys": active_keys
            },
            "daily_usage": {
                "requests_24h": daily_stats['total_requests'] or 0,
                "cache_hits_24h": daily_stats['total_hits'] or 0,
                "cache_misses_24h": daily_stats['total_misses'] or 0
            }
        }
    except Exception as e:
        error_log.exception(f"Admin system stats failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.post("/users/{tenant_id}/activate")
def activate_user(tenant_id: str, admin: bool = Depends(require_admin)):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("UPDATE api_keys SET is_active = TRUE WHERE tenant_id = %s RETURNING api_key", (tenant_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tenant not found")
            return {"success": True, "message": f"API key activated for tenant {tenant_id}"}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Admin activate user failed | tenant={tenant_id} | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_router.get("/health")
def get_admin_health(admin: bool = Depends(require_admin)):
    """Comprehensive health check for admin dashboard."""
    import time
    health = {"status": "healthy", "checks": {}}

    # Database check
    try:
        start = time.time()
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
        health["checks"]["database"] = {"status": "up", "latency_ms": round((time.time() - start) * 1000, 1)}
    except Exception as e:
        health["checks"]["database"] = {"status": "down", "error": str(type(e).__name__)}
        health["status"] = "degraded"

    # Cache engine check
    try:
        svc_instance = get_svc()
        health["checks"]["cache_engine"] = {
            "status": "up",
            "tenants": len(svc_instance.tenants),
            "total_entries": sum(len(t.rows) for t in svc_instance.tenants.values()),
        }
    except Exception as e:
        health["checks"]["cache_engine"] = {"status": "down", "error": str(type(e).__name__)}
        health["status"] = "degraded"

    # Redis check
    try:
        from semantic_cache_server import redis_client  # type: ignore[attr-defined]
        if redis_client:
            start = time.time()
            redis_client.ping()
            health["checks"]["redis"] = {"status": "up", "latency_ms": round((time.time() - start) * 1000, 1)}
        else:
            health["checks"]["redis"] = {"status": "not_configured"}
    except Exception as e:
        health["checks"]["redis"] = {"status": "down", "error": str(type(e).__name__)}

    # OpenAI check
    openai_key = os.getenv("OPENAI_API_KEY", "")
    health["checks"]["openai"] = {"status": "configured" if openai_key and not openai_key.startswith("sk-your") else "not_configured"}

    # Stripe check
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    health["checks"]["stripe"] = {"status": "configured" if stripe_key and "PASTE" not in stripe_key else "not_configured"}

    # Vector store check (Pinecone or FAISS fallback)
    try:
        from vector_store import health_check as vs_health
        health["checks"]["vector_store"] = vs_health()
    except Exception as e:
        health["checks"]["vector_store"] = {"status": "error", "error": str(type(e).__name__)}

    # Environment config
    health["config"] = {
        "encryption_key": bool(os.getenv("ENCRYPTION_KEY")),
        "encryption_salt": bool(os.getenv("ENCRYPTION_SALT")),
        "admin_api_key": bool(os.getenv("ADMIN_API_KEY")),
        "pinecone_api_key": bool(os.getenv("PINECONE_API_KEY")),
        "sentry_dsn": bool(os.getenv("SENTRY_DSN")),
        "resend_api_key": bool(os.getenv("RESEND_API_KEY")),
        "frontend_url": os.getenv("FRONTEND_URL", "not set"),
        "allowed_origins": os.getenv("ALLOWED_ORIGINS", "not set"),
    }

    return health


@admin_router.get("/audit-logs")
def list_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    admin: bool = Depends(require_admin)
):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            if action:
                cur.execute("""
                    SELECT al.*, p.email, p.name as user_name
                    FROM audit_logs al
                    LEFT JOIN profiles p ON al.user_id = p.id
                    WHERE al.action = %s
                    ORDER BY al.created_at DESC
                    LIMIT %s OFFSET %s
                """, (action, limit, offset))
            else:
                cur.execute("""
                    SELECT al.*, p.email, p.name as user_name
                    FROM audit_logs al
                    LEFT JOIN profiles p ON al.user_id = p.id
                    ORDER BY al.created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))

            logs = []
            for row in cur.fetchall():
                d = dict(row)
                d['created_at'] = str(d['created_at'])
                d['user_id'] = str(d['user_id']) if d['user_id'] else None
                d['org_id'] = str(d['org_id']) if d['org_id'] else None
                d['details'] = d['details'] or {}
                logs.append(d)

            # Get total count
            if action:
                cur.execute("SELECT COUNT(*) as count FROM audit_logs WHERE action = %s", (action,))
            else:
                cur.execute("SELECT COUNT(*) as count FROM audit_logs")
            total = cur.fetchone()['count']

            return {"total": total, "limit": limit, "offset": offset, "logs": logs}
    except Exception as e:
        error_log.exception(f"Admin audit logs failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")
