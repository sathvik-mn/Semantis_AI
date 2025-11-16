# 🚀 Running Services - Semantis AI

## ✅ Status: Both Services Running!

### 🔴 Backend API (RUNNING)

**URL**: http://localhost:8000

**Status**: ✅ **RUNNING** on port 8000

**Health Check**: http://localhost:8000/health
- Status: OK
- Service: semantic-cache
- Version: 0.1.0

### 🟢 Frontend Dashboard (RUNNING)

**URL**: http://localhost:3000

**Status**: ✅ **RUNNING** on port 3000

---

## 📊 Access Points

### Backend API

1. **API Documentation (Swagger UI)**
   - **URL**: http://localhost:8000/docs
   - **Description**: Interactive API documentation
   - **Features**: Try endpoints, see schemas, test authentication

2. **API Documentation (ReDoc)**
   - **URL**: http://localhost:8000/redoc
   - **Description**: Clean API documentation

3. **Health Check**
   - **URL**: http://localhost:8000/health
   - **Method**: GET
   - **Response**: `{"status": "ok", "service": "semantic-cache", "version": "0.1.0"}`

4. **Prometheus Metrics**
   - **URL**: http://localhost:8000/prometheus/metrics
   - **Method**: GET
   - **Description**: Prometheus metrics endpoint

5. **OpenAPI Specification**
   - **URL**: http://localhost:8000/openapi.json
   - **Method**: GET
   - **Description**: OpenAPI 3.1.0 specification

### Frontend Dashboard

1. **Main Dashboard**
   - **URL**: http://localhost:3000
   - **Description**: Main frontend dashboard
   - **Features**: Query playground, metrics, logs, settings

2. **Query Playground**
   - **URL**: http://localhost:3000/playground
   - **Description**: Test semantic cache queries

3. **Metrics Dashboard**
   - **URL**: http://localhost:3000/metrics
   - **Description**: View cache performance metrics

4. **Logs Viewer**
   - **URL**: http://localhost:3000/logs
   - **Description**: View cache event logs

5. **Settings Panel**
   - **URL**: http://localhost:3000/settings
   - **Description**: Configure API key and settings

6. **Documentation**
   - **URL**: http://localhost:3000/docs
   - **Description**: API documentation and integration guides

---

## 🔑 Authentication

### User API Keys

**Format**: `Bearer sc-{tenant}-{anything}`

**Example**: `Bearer sc-test-local`

**Usage**: Include in `Authorization` header for all authenticated endpoints

### Admin API Keys

**Format**: `?api_key=<ADMIN_API_KEY>`

**Default**: `admin-secret-key-change-me` (set via `ADMIN_API_KEY` environment variable)

**Usage**: Include as query parameter for all admin endpoints

---

## 📡 API Endpoints

### Core API

- **GET** `/health` - Health check
- **GET** `/metrics` - Cache metrics (requires auth)
- **GET** `/query?prompt=...` - Simple query (requires auth)
- **GET** `/events?limit=N` - Cache events (requires auth)
- **POST** `/v1/chat/completions` - OpenAI-compatible API (requires auth)

### Admin API

- **GET** `/admin/analytics/summary?api_key=...` - Analytics summary
- **GET** `/admin/analytics/user-growth?api_key=...` - User growth
- **GET** `/admin/analytics/plan-distribution?api_key=...` - Plan distribution
- **GET** `/admin/analytics/usage-trends?api_key=...` - Usage trends
- **GET** `/admin/analytics/top-users?api_key=...` - Top users
- **GET** `/admin/users?api_key=...` - List all users
- **GET** `/admin/users/{tenant_id}/details?api_key=...` - User details
- **POST** `/admin/users/{tenant_id}/update-plan?api_key=...` - Update plan
- **POST** `/admin/users/{tenant_id}/deactivate?api_key=...` - Deactivate user
- **GET** `/admin/system/stats?api_key=...` - System statistics

---

## 🧪 Quick Test

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# Test query (requires API key)
curl -X GET "http://localhost:8000/query?prompt=What%20is%20Python?" \
  -H "Authorization: Bearer sc-test-local"

# Test admin API
curl "http://localhost:8000/admin/analytics/summary?api_key=admin-secret-key-change-me"
```

### Test Frontend

1. Open http://localhost:3000 in browser
2. Enter API key: `sc-test-local`
3. Try a query in the playground
4. View metrics and logs

---

## 📝 Summary

### ✅ Running Services

- **Backend**: ✅ http://localhost:8000
- **Frontend**: ✅ http://localhost:3000

### 🔗 Quick Links

- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health**: http://localhost:8000/health
- **Frontend Dashboard**: http://localhost:3000
- **Admin API**: http://localhost:8000/admin/* (with api_key)

### 🎯 Next Steps

1. **Test Backend**: Visit http://localhost:8000/docs
2. **Test Frontend**: Visit http://localhost:3000
3. **Enter API Key**: Use `sc-test-local` for testing
4. **Try Queries**: Test semantic cache in playground
5. **View Metrics**: Check cache performance

---

## 🎉 You're Ready to Go!

Both services are running and ready for testing! 🚀

**Backend**: http://localhost:8000
**Frontend**: http://localhost:3000

Enjoy testing your semantic cache application! 🎊



