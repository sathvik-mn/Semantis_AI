"""
Admin API Endpoints for Dashboard
Provides comprehensive analytics, user management, and business insights
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel
import os
from database import (
    get_db_connection, list_api_keys, get_usage_stats,
    get_api_key_info, update_plan, deactivate_api_key
)
# Import logging directly to avoid circular dependency
import logging

# Get loggers by name (to avoid circular import)
def get_logger(name):
    logger = logging.getLogger(name)
    return logger

system_log = get_logger("system")
app_log = get_logger("application")
error_log = get_logger("errors")

# Import svc lazily to avoid circular dependency
def get_svc():
    from semantic_cache_server import svc
    return svc

# Admin API Router
admin_router = APIRouter(prefix="/admin", tags=["admin"])

# Admin API Key (set via environment variable)
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "admin-secret-key-change-me")

def verify_admin_key(api_key: str = Query(...)):
    """Verify admin API key."""
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin API key")
    return True

def require_admin(admin_verified: bool = Depends(verify_admin_key)):
    """Dependency to require admin authentication."""
    return admin_verified

# -----------------------------
# Analytics & Statistics Models
# -----------------------------
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

class UserGrowthStats(BaseModel):
    period: str  # "daily", "weekly", "monthly"
    data: List[Dict]  # [{date, count, new_users}, ...]

class PlanStats(BaseModel):
    plan: str
    count: int
    percentage: float
    total_requests: int
    total_cost: float

class TenantDetails(BaseModel):
    tenant_id: str
    api_key: str
    email: Optional[str]
    name: Optional[str]
    plan: str
    plan_expires_at: Optional[str]
    is_active: bool
    created_at: str
    last_used_at: Optional[str]
    usage_count: int
    cache_stats: Dict

# -----------------------------
# Analytics Endpoints
# -----------------------------
@admin_router.get("/analytics/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    admin: bool = Depends(require_admin)
):
    """Get overall analytics summary."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(DISTINCT id) as count FROM users")
            total_users = cursor.fetchone()['count']
            
            # Total API keys
            cursor.execute("SELECT COUNT(*) as count FROM api_keys")
            total_api_keys = cursor.fetchone()['count']
            
            # Active users (used in last N days)
            cursor.execute("""
                SELECT COUNT(DISTINCT tenant_id) as count
                FROM api_keys
                WHERE is_active = 1 
                AND (last_used_at >= datetime('now', '-' || ? || ' days') OR last_used_at IS NULL)
            """, (days,))
            active_users = cursor.fetchone()['count']
            
            # Usage statistics
            cursor.execute("""
                SELECT 
                    SUM(request_count) as total_requests,
                    SUM(cache_hits) as total_hits,
                    SUM(cache_misses) as total_misses,
                    SUM(tokens_used) as total_tokens,
                    SUM(cost_estimate) as total_cost
                FROM usage_logs
                WHERE logged_at >= datetime('now', '-' || ? || ' days')
            """, (days,))
            usage = cursor.fetchone()
            
            total_requests = usage['total_requests'] or 0
            total_hits = usage['total_hits'] or 0
            total_misses = usage['total_misses'] or 0
            total_tokens = usage['total_tokens'] or 0
            total_cost = usage['total_cost'] or 0
            
            hit_ratio = (total_hits / total_requests * 100) if total_requests > 0 else 0.0
            
            app_log.info(f"Admin | analytics summary | days={days}")
            
            return AnalyticsSummary(
                total_users=total_users,
                total_api_keys=total_api_keys,
                active_users=active_users,
                total_requests=total_requests,
                total_cache_hits=total_hits,
                total_cache_misses=total_misses,
                cache_hit_ratio=round(hit_ratio, 2),
                total_tokens_used=total_tokens,
                total_cost_estimate=round(total_cost, 2)
            )
    except Exception as e:
        error_log.exception(f"Admin analytics summary failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/analytics/user-growth")
def get_user_growth(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=1, le=365),
    admin: bool = Depends(require_admin)
):
    """Get user growth statistics over time."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Determine date format based on period
            if period == "daily":
                date_format = "date(created_at)"
                group_by = "date(created_at)"
            elif period == "weekly":
                date_format = "strftime('%Y-W%W', created_at)"
                group_by = "strftime('%Y-W%W', created_at)"
            else:  # monthly
                date_format = "strftime('%Y-%m', created_at)"
                group_by = "strftime('%Y-%m', created_at)"
            
            # Get user growth
            cursor.execute(f"""
                SELECT 
                    {date_format} as period,
                    COUNT(*) as new_users
                FROM users
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY {group_by}
                ORDER BY period ASC
            """, (days,))
            
            user_growth = [dict(row) for row in cursor.fetchall()]
            
            # Get API key growth (users who generated keys)
            cursor.execute(f"""
                SELECT 
                    {date_format} as period,
                    COUNT(DISTINCT tenant_id) as new_keys
                FROM api_keys
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY {group_by}
                ORDER BY period ASC
            """, (days,))
            
            key_growth = {row['period']: row['new_keys'] for row in cursor.fetchall()}
            
            # Combine data
            result = []
            for row in user_growth:
                result.append({
                    "date": row['period'],
                    "new_users": row['new_users'],
                    "new_api_keys": key_growth.get(row['period'], 0),
                    "total_users": sum(r['new_users'] for r in user_growth if r['period'] <= row['period'])
                })
            
            app_log.info(f"Admin | user growth | period={period} | days={days}")
            
            return {
                "period": period,
                "days": days,
                "data": result
            }
    except Exception as e:
        error_log.exception(f"Admin user growth failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/analytics/plan-distribution")
def get_plan_distribution(admin: bool = Depends(require_admin)):
    """Get subscription plan distribution statistics."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get plan counts
            cursor.execute("""
                SELECT 
                    plan,
                    COUNT(*) as count,
                    SUM(usage_count) as total_requests
                FROM api_keys
                WHERE is_active = 1
                GROUP BY plan
            """)
            
            plans = [dict(row) for row in cursor.fetchall()]
            total_active = sum(p['count'] for p in plans)
            
            # Get cost per plan
            cursor.execute("""
                SELECT 
                    ak.plan,
                    SUM(ul.cost_estimate) as total_cost
                FROM api_keys ak
                LEFT JOIN usage_logs ul ON ak.api_key = ul.api_key
                WHERE ak.is_active = 1
                GROUP BY ak.plan
            """)
            costs = {row['plan']: row['total_cost'] or 0 for row in cursor.fetchall()}
            
            # Build result
            result = []
            for plan in plans:
                percentage = (plan['count'] / total_active * 100) if total_active > 0 else 0
                result.append({
                    "plan": plan['plan'],
                    "count": plan['count'],
                    "percentage": round(percentage, 2),
                    "total_requests": plan['total_requests'] or 0,
                    "total_cost": round(costs.get(plan['plan'], 0), 2)
                })
            
            app_log.info("Admin | plan distribution")
            
            return {
                "total_active_keys": total_active,
                "plans": result
            }
    except Exception as e:
        error_log.exception(f"Admin plan distribution failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/analytics/usage-trends")
def get_usage_trends(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=1, le=365),
    admin: bool = Depends(require_admin)
):
    """Get usage trends over time."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Determine date format
            if period == "daily":
                date_format = "date(logged_at)"
                group_by = "date(logged_at)"
            elif period == "weekly":
                date_format = "strftime('%Y-W%W', logged_at)"
                group_by = "strftime('%Y-W%W', logged_at)"
            else:  # monthly
                date_format = "strftime('%Y-%m', logged_at)"
                group_by = "strftime('%Y-%m', logged_at)"
            
            cursor.execute(f"""
                SELECT 
                    {date_format} as period,
                    SUM(request_count) as requests,
                    SUM(cache_hits) as hits,
                    SUM(cache_misses) as misses,
                    SUM(tokens_used) as tokens,
                    SUM(cost_estimate) as cost
                FROM usage_logs
                WHERE logged_at >= datetime('now', '-' || ? || ' days')
                GROUP BY {group_by}
                ORDER BY period ASC
            """, (days,))
            
            trends = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                total_reqs = row_dict['requests'] or 0
                hits = row_dict['hits'] or 0
                hit_ratio = (hits / total_reqs * 100) if total_reqs > 0 else 0
                
                trends.append({
                    "date": row_dict['period'],
                    "requests": total_reqs,
                    "cache_hits": hits,
                    "cache_misses": row_dict['misses'] or 0,
                    "cache_hit_ratio": round(hit_ratio, 2),
                    "tokens_used": row_dict['tokens'] or 0,
                    "cost_estimate": round(row_dict['cost'] or 0, 2)
                })
            
            app_log.info(f"Admin | usage trends | period={period} | days={days}")
            
            return {
                "period": period,
                "days": days,
                "data": trends
            }
    except Exception as e:
        error_log.exception(f"Admin usage trends failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/analytics/top-users")
def get_top_users(
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("usage_count", regex="^(usage_count|requests|cost)$"),
    days: int = Query(30, ge=1, le=365),
    admin: bool = Depends(require_admin)
):
    """Get top users by usage."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if sort_by == "usage_count":
                order_by = "ak.usage_count DESC"
            elif sort_by == "requests":
                order_by = "total_requests DESC"
            else:  # cost
                order_by = "total_cost DESC"
            
            cursor.execute(f"""
                SELECT 
                    ak.tenant_id,
                    ak.api_key,
                    ak.plan,
                    ak.usage_count,
                    u.email,
                    u.name,
                    ak.created_at,
                    ak.last_used_at,
                    COALESCE(SUM(ul.request_count), 0) as total_requests,
                    COALESCE(SUM(ul.cache_hits), 0) as total_hits,
                    COALESCE(SUM(ul.cache_misses), 0) as total_misses,
                    COALESCE(SUM(ul.tokens_used), 0) as total_tokens,
                    COALESCE(SUM(ul.cost_estimate), 0) as total_cost
                FROM api_keys ak
                LEFT JOIN users u ON ak.user_id = u.id
                LEFT JOIN usage_logs ul ON ak.api_key = ul.api_key 
                    AND ul.logged_at >= datetime('now', '-' || ? || ' days')
                WHERE ak.is_active = 1
                GROUP BY ak.api_key
                ORDER BY {order_by}
                LIMIT ?
            """, (days, limit))
            
            users = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                total_reqs = row_dict['total_requests'] or 0
                hits = row_dict['total_hits'] or 0
                hit_ratio = (hits / total_reqs * 100) if total_reqs > 0 else 0
                
                users.append({
                    "tenant_id": row_dict['tenant_id'],
                    "api_key": row_dict['api_key'][:20] + "..." if len(row_dict['api_key']) > 20 else row_dict['api_key'],
                    "email": row_dict['email'],
                    "name": row_dict['name'],
                    "plan": row_dict['plan'],
                    "usage_count": row_dict['usage_count'],
                    "created_at": row_dict['created_at'],
                    "last_used_at": row_dict['last_used_at'],
                    "total_requests": total_reqs,
                    "total_cache_hits": hits,
                    "total_cache_misses": row_dict['total_misses'] or 0,
                    "cache_hit_ratio": round(hit_ratio, 2),
                    "total_tokens": row_dict['total_tokens'] or 0,
                    "total_cost": round(row_dict['total_cost'] or 0, 2)
                })
            
            app_log.info(f"Admin | top users | limit={limit} | sort_by={sort_by}")
            
            return {
                "limit": limit,
                "sort_by": sort_by,
                "days": days,
                "users": users
            }
    except Exception as e:
        error_log.exception(f"Admin top users failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# User Management Endpoints
# -----------------------------
@admin_router.get("/users")
def list_all_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    admin: bool = Depends(require_admin)
):
    """List all users with pagination and search."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if search:
                cursor.execute("""
                    SELECT 
                        u.*,
                        COUNT(DISTINCT ak.id) as api_key_count,
                        SUM(ak.usage_count) as total_usage,
                        MAX(ak.last_used_at) as last_used_at
                    FROM users u
                    LEFT JOIN api_keys ak ON u.id = ak.user_id
                    WHERE u.email LIKE ? OR u.name LIKE ?
                    GROUP BY u.id
                    ORDER BY u.created_at DESC
                    LIMIT ? OFFSET ?
                """, (f"%{search}%", f"%{search}%", limit, offset))
            else:
                cursor.execute("""
                    SELECT 
                        u.*,
                        COUNT(DISTINCT ak.id) as api_key_count,
                        SUM(ak.usage_count) as total_usage,
                        MAX(ak.last_used_at) as last_used_at
                    FROM users u
                    LEFT JOIN api_keys ak ON u.id = ak.user_id
                    GROUP BY u.id
                    ORDER BY u.created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            users = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                users.append({
                    "id": row_dict['id'],
                    "email": row_dict['email'],
                    "name": row_dict['name'],
                    "created_at": row_dict['created_at'],
                    "updated_at": row_dict['updated_at'],
                    "api_key_count": row_dict['api_key_count'] or 0,
                    "total_usage": row_dict['total_usage'] or 0,
                    "last_used_at": row_dict['last_used_at']
                })
            
            # Get total count
            if search:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM users
                    WHERE email LIKE ? OR name LIKE ?
                """, (f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("SELECT COUNT(*) as count FROM users")
            
            total = cursor.fetchone()['count']
            
            app_log.info(f"Admin | list users | limit={limit} | offset={offset} | search={search}")
            
            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "users": users
            }
    except Exception as e:
        error_log.exception(f"Admin list users failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/users/{tenant_id}/details")
def get_user_details(tenant_id: str, admin: bool = Depends(require_admin)):
    """Get detailed information about a specific tenant/user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get API key info
            cursor.execute("""
                SELECT ak.*, u.email, u.name
                FROM api_keys ak
                LEFT JOIN users u ON ak.user_id = u.id
                WHERE ak.tenant_id = ?
                ORDER BY ak.created_at DESC
                LIMIT 1
            """, (tenant_id,))
            
            key_info = cursor.fetchone()
            if not key_info:
                raise HTTPException(status_code=404, detail="Tenant not found")
            
            key_dict = dict(key_info)
            
            # Get usage statistics
            usage_stats = get_usage_stats(tenant_id, days=30)
            
            # Get cache statistics from semantic cache service
            cache_stats = {}
            try:
                svc_instance = get_svc()
                cache_stats = svc_instance.metrics(tenant_id)
            except:
                cache_stats = {}
            
            # Get recent activity
            cursor.execute("""
                SELECT 
                    endpoint,
                    SUM(request_count) as requests,
                    SUM(cache_hits) as hits,
                    SUM(cache_misses) as misses,
                    SUM(tokens_used) as tokens,
                    SUM(cost_estimate) as cost
                FROM usage_logs
                WHERE tenant_id = ?
                AND logged_at >= datetime('now', '-7 days')
                GROUP BY endpoint
            """, (tenant_id,))
            
            recent_activity = [dict(row) for row in cursor.fetchall()]
            
            app_log.info(f"Admin | user details | tenant={tenant_id}")
            
            return {
                "tenant_id": tenant_id,
                "api_key": key_dict['api_key'][:20] + "..." if len(key_dict['api_key']) > 20 else key_dict['api_key'],
                "email": key_dict['email'],
                "name": key_dict['name'],
                "plan": key_dict['plan'],
                "plan_expires_at": key_dict['plan_expires_at'],
                "is_active": bool(key_dict['is_active']),
                "created_at": key_dict['created_at'],
                "last_used_at": key_dict['last_used_at'],
                "usage_count": key_dict['usage_count'],
                "usage_stats_30d": usage_stats,
                "cache_stats": cache_stats,
                "recent_activity": recent_activity
            }
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Admin user details failed | tenant={tenant_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Plan Management Endpoints
# -----------------------------
@admin_router.post("/users/{tenant_id}/update-plan")
def update_user_plan(
    tenant_id: str,
    plan: str = Query(...),
    expires_at: Optional[str] = Query(None),
    admin: bool = Depends(require_admin)
):
    """Update a user's subscription plan."""
    try:
        success = update_plan(tenant_id, plan, expires_at)
        if success:
            app_log.info(f"Admin | plan updated | tenant={tenant_id} | plan={plan}")
            return {"success": True, "message": f"Plan updated to {plan} for tenant {tenant_id}"}
        else:
            raise HTTPException(status_code=404, detail="Tenant not found")
    except Exception as e:
        error_log.exception(f"Admin plan update failed | tenant={tenant_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/users/{tenant_id}/deactivate")
def deactivate_user(
    tenant_id: str,
    admin: bool = Depends(require_admin)
):
    """Deactivate a user's API key."""
    try:
        # Get API key for tenant
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT api_key FROM api_keys WHERE tenant_id = ?", (tenant_id,))
            key_row = cursor.fetchone()
            if not key_row:
                raise HTTPException(status_code=404, detail="Tenant not found")
            
            api_key = key_row['api_key']
            success = deactivate_api_key(api_key)
            if success:
                app_log.info(f"Admin | user deactivated | tenant={tenant_id}")
                return {"success": True, "message": f"API key deactivated for tenant {tenant_id}"}
            else:
                raise HTTPException(status_code=500, detail="Failed to deactivate")
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Admin deactivate user failed | tenant={tenant_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# System Statistics
# -----------------------------
@admin_router.get("/system/stats")
def get_system_stats(admin: bool = Depends(require_admin)):
    """Get system-wide statistics."""
    try:
        # Cache statistics
        svc_instance = get_svc()
        total_tenants = len(svc_instance.tenants)
        total_entries = sum(len(t.rows) for t in svc_instance.tenants.values())
        
        # Database statistics
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM users")
            total_users = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM api_keys WHERE is_active = 1")
            active_keys = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT 
                    SUM(request_count) as total_requests,
                    SUM(cache_hits) as total_hits,
                    SUM(cache_misses) as total_misses
                FROM usage_logs
                WHERE logged_at >= datetime('now', '-24 hours')
            """)
            daily_stats = cursor.fetchone()
            
            system_log.info("Admin | system stats")
        
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
        error_log.exception(f"Admin system stats failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

