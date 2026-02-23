"""
Admin API Endpoints for Dashboard
Provides comprehensive analytics, user management, and business insights.
Uses Supabase Postgres via psycopg2.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict
from pydantic import BaseModel
import os
from psycopg2.extras import RealDictCursor
from database import (
    get_db_connection, list_api_keys, get_usage_stats,
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

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "admin-secret-key-change-me")

def verify_admin_key(api_key: str = Query(...)):
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin API key")
    return True

def require_admin(admin_verified: bool = Depends(verify_admin_key)):
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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/analytics/plan-distribution")
def get_plan_distribution(admin: bool = Depends(require_admin)):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT plan, COUNT(*) as count, COALESCE(SUM(usage_count), 0) as total_requests
                FROM api_keys WHERE is_active = TRUE
                GROUP BY plan
            """)
            plans = [dict(row) for row in cur.fetchall()]
            total_active = sum(p['count'] for p in plans)

            cur.execute("""
                SELECT ak.plan, COALESCE(SUM(ul.cost_estimate), 0) as total_cost
                FROM api_keys ak
                LEFT JOIN usage_logs ul ON ak.api_key = ul.api_key
                WHERE ak.is_active = TRUE
                GROUP BY ak.plan
            """)
            costs = {row['plan']: row['total_cost'] or 0 for row in cur.fetchall()}

            result = []
            for plan in plans:
                pct = (plan['count'] / total_active * 100) if total_active > 0 else 0
                result.append({
                    "plan": plan['plan'],
                    "count": plan['count'],
                    "percentage": round(pct, 2),
                    "total_requests": plan['total_requests'] or 0,
                    "total_cost": round(costs.get(plan['plan'], 0), 2)
                })

            return {"total_active_keys": total_active, "plans": result}
    except Exception as e:
        error_log.exception(f"Admin plan distribution failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/analytics/top-users")
def get_top_users(
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("usage_count", regex="^(usage_count|requests|cost)$"),
    days: int = Query(30, ge=1, le=365),
    admin: bool = Depends(require_admin)
):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            if sort_by == "usage_count":
                order_by = "ak.usage_count DESC"
            elif sort_by == "requests":
                order_by = "total_requests DESC"
            else:
                order_by = "total_cost DESC"

            cur.execute(f"""
                SELECT
                    ak.tenant_id, ak.api_key, ak.plan, ak.usage_count,
                    p.email, p.name,
                    ak.created_at, ak.last_used_at,
                    COALESCE(SUM(ul.request_count), 0) as total_requests,
                    COALESCE(SUM(ul.cache_hits), 0) as total_hits,
                    COALESCE(SUM(ul.cache_misses), 0) as total_misses,
                    COALESCE(SUM(ul.tokens_used), 0) as total_tokens,
                    COALESCE(SUM(ul.cost_estimate), 0) as total_cost
                FROM api_keys ak
                LEFT JOIN profiles p ON ak.user_id = p.id
                LEFT JOIN usage_logs ul ON ak.api_key = ul.api_key
                    AND ul.logged_at >= NOW() - INTERVAL '1 day' * %s
                WHERE ak.is_active = TRUE
                GROUP BY ak.id, ak.tenant_id, ak.api_key, ak.plan,
                         ak.usage_count, p.email, p.name,
                         ak.created_at, ak.last_used_at
                ORDER BY {order_by}
                LIMIT %s
            """, (days, limit))

            users = []
            for row in cur.fetchall():
                d = dict(row)
                total_reqs = d['total_requests'] or 0
                hits = d['total_hits'] or 0
                hit_ratio = (hits / total_reqs * 100) if total_reqs > 0 else 0
                users.append({
                    "tenant_id": d['tenant_id'],
                    "api_key": d['api_key'][:20] + "..." if len(d['api_key']) > 20 else d['api_key'],
                    "email": d['email'],
                    "name": d['name'],
                    "plan": d['plan'],
                    "usage_count": d['usage_count'],
                    "created_at": str(d['created_at']),
                    "last_used_at": str(d['last_used_at']) if d['last_used_at'] else None,
                    "total_requests": total_reqs,
                    "total_cache_hits": hits,
                    "total_cache_misses": d['total_misses'] or 0,
                    "cache_hit_ratio": round(hit_ratio, 2),
                    "total_tokens": d['total_tokens'] or 0,
                    "total_cost": round(d['total_cost'] or 0, 2)
                })

            return {"limit": limit, "sort_by": sort_by, "days": days, "users": users}
    except Exception as e:
        error_log.exception(f"Admin top users failed | error={e}")
        raise HTTPException(status_code=500, detail=str(e))


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

            if search:
                cur.execute("""
                    SELECT
                        p.id, p.email, p.name, p.created_at, p.updated_at,
                        COUNT(DISTINCT ak.id) as api_key_count,
                        COALESCE(SUM(ak.usage_count), 0) as total_usage,
                        MAX(ak.last_used_at) as last_used_at
                    FROM profiles p
                    LEFT JOIN api_keys ak ON p.id = ak.user_id
                    WHERE p.email ILIKE %s OR p.name ILIKE %s
                    GROUP BY p.id
                    ORDER BY p.created_at DESC
                    LIMIT %s OFFSET %s
                """, (f"%{search}%", f"%{search}%", limit, offset))
            else:
                cur.execute("""
                    SELECT
                        p.id, p.email, p.name, p.created_at, p.updated_at,
                        COUNT(DISTINCT ak.id) as api_key_count,
                        COALESCE(SUM(ak.usage_count), 0) as total_usage,
                        MAX(ak.last_used_at) as last_used_at
                    FROM profiles p
                    LEFT JOIN api_keys ak ON p.id = ak.user_id
                    GROUP BY p.id
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
                    "total_usage": d['total_usage'] or 0,
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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))
