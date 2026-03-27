# Admin API Documentation

Complete API reference for the admin dashboard backend.

## Authentication

All admin endpoints require authentication via query parameter:
```
?api_key=<ADMIN_API_KEY>
```

**Admin API Key** is set via environment variable `ADMIN_API_KEY` (default: "admin-secret-key-change-me")

## Base URL

```
http://localhost:8000/admin
```

## Endpoints

### 1. Analytics Summary

**GET** `/admin/analytics/summary`

Get overall analytics summary.

**Query Parameters:**
- `api_key` (required): Admin API key
- `days` (optional): Number of days to analyze (default: 30, range: 1-365)

**Response:**
```json
{
  "total_users": 150,
  "total_api_keys": 175,
  "active_users": 120,
  "total_requests": 45000,
  "total_cache_hits": 36000,
  "total_cache_misses": 9000,
  "cache_hit_ratio": 80.0,
  "total_tokens_used": 4500000,
  "total_cost_estimate": 1250.50
}
```

---

### 2. User Growth Statistics

**GET** `/admin/analytics/user-growth`

Get user growth over time.

**Query Parameters:**
- `api_key` (required): Admin API key
- `period` (optional): "daily" | "weekly" | "monthly" (default: "daily")
- `days` (optional): Number of days to look back (default: 30, range: 1-365)

**Response:**
```json
{
  "period": "daily",
  "days": 30,
  "data": [
    {
      "date": "2024-01-15",
      "new_users": 5,
      "new_api_keys": 8,
      "total_users": 150
    }
  ]
}
```

---

### 3. Plan Distribution

**GET** `/admin/analytics/plan-distribution`

Get subscription plan distribution.

**Query Parameters:**
- `api_key` (required): Admin API key

**Response:**
```json
{
  "total_active_keys": 175,
  "plans": [
    {
      "plan": "free",
      "count": 120,
      "percentage": 68.57,
      "total_requests": 30000,
      "total_cost": 500.00
    }
  ]
}
```

---

### 4. Usage Trends

**GET** `/admin/analytics/usage-trends`

Get usage trends over time.

**Query Parameters:**
- `api_key` (required): Admin API key
- `period` (optional): "daily" | "weekly" | "monthly" (default: "daily")
- `days` (optional): Number of days (default: 30, range: 1-365)

**Response:**
```json
{
  "period": "daily",
  "days": 30,
  "data": [
    {
      "date": "2024-01-15",
      "requests": 1500,
      "cache_hits": 1200,
      "cache_misses": 300,
      "cache_hit_ratio": 80.0,
      "tokens_used": 150000,
      "cost_estimate": 41.67
    }
  ]
}
```

---

### 5. Top Users

**GET** `/admin/analytics/top-users`

Get top users by usage.

**Query Parameters:**
- `api_key` (required): Admin API key
- `limit` (optional): Number of users (default: 10, range: 1-100)
- `sort_by` (optional): "usage_count" | "requests" | "cost" (default: "usage_count")
- `days` (optional): Days to look back (default: 30, range: 1-365)

**Response:**
```json
{
  "limit": 10,
  "sort_by": "usage_count",
  "days": 30,
  "users": [
    {
      "tenant_id": "user123",
      "api_key": "sc-user123-abc...",
      "email": "user@example.com",
      "name": "John Doe",
      "plan": "pro",
      "usage_count": 5000,
      "created_at": "2024-01-01T10:00:00",
      "last_used_at": "2024-01-15T15:30:00",
      "total_requests": 5000,
      "total_cache_hits": 4000,
      "total_cache_misses": 1000,
      "cache_hit_ratio": 80.0,
      "total_tokens": 500000,
      "total_cost": 138.89
    }
  ]
}
```

---

### 6. List All Users

**GET** `/admin/users`

List all users with pagination.

**Query Parameters:**
- `api_key` (required): Admin API key
- `limit` (optional): Users per page (default: 100, range: 1-1000)
- `offset` (optional): Pagination offset (default: 0)
- `search` (optional): Search term (email or name)

**Response:**
```json
{
  "total": 150,
  "limit": 100,
  "offset": 0,
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "created_at": "2024-01-01T10:00:00",
      "updated_at": "2024-01-15T15:30:00",
      "api_key_count": 2,
      "total_usage": 5000,
      "last_used_at": "2024-01-15T15:30:00"
    }
  ]
}
```

---

### 7. User Details

**GET** `/admin/users/{tenant_id}/details`

Get detailed user information.

**Query Parameters:**
- `api_key` (required): Admin API key

**Path Parameters:**
- `tenant_id`: Tenant identifier

**Response:**
```json
{
  "tenant_id": "user123",
  "api_key": "sc-user123-abc...",
  "email": "user@example.com",
  "name": "John Doe",
  "plan": "pro",
  "plan_expires_at": "2024-12-31T23:59:59",
  "is_active": true,
  "created_at": "2024-01-01T10:00:00",
  "last_used_at": "2024-01-15T15:30:00",
  "usage_count": 5000,
  "usage_stats_30d": {
    "total_requests": 5000,
    "total_hits": 4000,
    "total_misses": 1000,
    "total_tokens": 500000,
    "total_cost": 138.89
  },
  "cache_stats": {
    "tenant": "user123",
    "requests": 5000,
    "hits": 4000,
    "semantic_hits": 3500,
    "misses": 1000,
    "hit_ratio": 0.8,
    "semantic_hit_ratio": 0.7,
    "avg_latency_ms": 150.5,
    "sim_threshold": 0.72,
    "entries": 450
  },
  "recent_activity": [
    {
      "endpoint": "/v1/chat/completions",
      "requests": 4500,
      "hits": 3600,
      "misses": 900,
      "tokens": 450000,
      "cost": 125.00
    }
  ]
}
```

---

### 8. Update User Plan

**POST** `/admin/users/{tenant_id}/update-plan`

Update a user's subscription plan.

**Query Parameters:**
- `api_key` (required): Admin API key
- `plan` (required): New plan name (e.g., "free", "pro", "enterprise")
- `expires_at` (optional): Expiration date (ISO format)

**Path Parameters:**
- `tenant_id`: Tenant identifier

**Response:**
```json
{
  "success": true,
  "message": "Plan updated to pro for tenant user123"
}
```

---

### 9. Deactivate User

**POST** `/admin/users/{tenant_id}/deactivate`

Deactivate a user's API key.

**Query Parameters:**
- `api_key` (required): Admin API key

**Path Parameters:**
- `tenant_id`: Tenant identifier

**Response:**
```json
{
  "success": true,
  "message": "API key deactivated for tenant user123"
}
```

---

### 10. System Statistics

**GET** `/admin/system/stats`

Get system-wide statistics.

**Query Parameters:**
- `api_key` (required): Admin API key

**Response:**
```json
{
  "cache": {
    "total_tenants": 175,
    "total_cache_entries": 12500,
    "avg_entries_per_tenant": 71.43
  },
  "database": {
    "total_users": 150,
    "active_api_keys": 175
  },
  "daily_usage": {
    "requests_24h": 1500,
    "cache_hits_24h": 1200,
    "cache_misses_24h": 300
  }
}
```

---

## Error Responses

All endpoints may return these error codes:

- **401 Unauthorized**: Invalid or missing admin API key
- **404 Not Found**: Resource not found (e.g., tenant_id not found)
- **500 Internal Server Error**: Server error

**Error Response Format:**
```json
{
  "detail": "Error message here"
}
```

---

## Testing Endpoints

You can test the endpoints using curl:

```bash
# Get analytics summary
curl "http://localhost:8000/admin/analytics/summary?api_key=admin-secret-key-change-me&days=30"

# Get user growth
curl "http://localhost:8000/admin/analytics/user-growth?api_key=admin-secret-key-change-me&period=daily&days=30"

# List users
curl "http://localhost:8000/admin/users?api_key=admin-secret-key-change-me&limit=10"
```

---

## Configuration

Set the admin API key in your `.env` file:

```bash
ADMIN_API_KEY=your-secure-admin-key-here
```

Or set it as an environment variable:

```bash
export ADMIN_API_KEY=your-secure-admin-key-here
```

---

## Security Notes

1. **Admin API Key**: Keep the admin API key secure and never expose it in frontend code
2. **HTTPS**: In production, always use HTTPS
3. **Rate Limiting**: Consider adding rate limiting for admin endpoints
4. **IP Whitelist**: Consider restricting admin endpoints to specific IP addresses

