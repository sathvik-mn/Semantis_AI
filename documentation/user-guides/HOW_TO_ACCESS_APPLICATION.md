# How to Access the Semantis AI Application

## 🚀 Quick Access Guide

### 1. Backend API (Already Running)
- **URL:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **OpenAPI Spec:** http://localhost:8000/openapi.json
- **Health Check:** http://localhost:8000/health

### 2. Frontend Dashboard (Needs to be Started)
- **URL:** http://localhost:5173 (or next available port)
- **Status:** Needs to be started manually

## 📋 Step-by-Step Access Instructions

### Step 1: Start the Frontend

Open a terminal and run:

```bash
cd frontend
npm run dev
```

You should see output like:
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 2: Access the Frontend Dashboard

1. Open your web browser
2. Navigate to: **http://localhost:5173**
3. You should see the Semantis AI dashboard

### Step 3: Set Up API Key

1. In the frontend, look for the API key settings
2. Enter an API key in the format: `sc-{tenant}-{anything}`
   - Example: `sc-test-local`
   - Example: `sc-demo-123`
3. Save the API key

### Step 4: Use the Application

#### Features Available:

1. **Query Playground**
   - Test LLM queries
   - See cache hits/misses in real-time
   - View response times

2. **Metrics Dashboard**
   - View cache performance metrics
   - Hit ratios (exact + semantic)
   - Latency statistics
   - Token savings estimates

3. **Events/Logs**
   - View recent cache events
   - See exact, semantic, and miss decisions
   - Download events as CSV

4. **Documentation**
   - API documentation
   - Usage examples
   - Integration guides

## 🔍 Accessing Backend Directly

### API Documentation (Swagger UI)
- **URL:** http://localhost:8000/docs
- **Features:**
  - Interactive API testing
  - Try out endpoints directly
  - View request/response schemas
  - Test authentication

### Alternative API Docs (ReDoc)
- **URL:** http://localhost:8000/redoc
- **Features:**
  - Clean documentation interface
  - Better for reading (less interactive)

### Health Check
- **URL:** http://localhost:8000/health
- **Response:**
  ```json
  {
    "status": "ok",
    "service": "semantic-cache",
    "version": "0.1.0"
  }
  ```

### Test Endpoints

#### 1. Get Metrics
```bash
curl -H "Authorization: Bearer sc-test-local" http://localhost:8000/metrics
```

#### 2. Get Events
```bash
curl -H "Authorization: Bearer sc-test-local" http://localhost:8000/events?limit=10
```

#### 3. Simple Query
```bash
curl -H "Authorization: Bearer sc-test-local" "http://localhost:8000/query?prompt=What%20is%20AI?"
```

#### 4. Chat Completion (OpenAI-compatible)
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sc-test-local" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "What is semantic caching?"}]
  }'
```

## 🖥️ Frontend Features

### Main Pages:

1. **Home/Dashboard**
   - Overview of cache performance
   - Quick stats and KPIs

2. **Playground**
   - Test queries interactively
   - See cache behavior in real-time
   - View responses and metadata

3. **Metrics**
   - Detailed performance metrics
   - Charts and visualizations
   - Historical data

4. **Logs/Events**
   - Recent cache events
   - Filter by type (exact/semantic/miss)
   - Export data

5. **Documentation**
   - API documentation
   - Integration guides
   - Code examples

## 🔐 Authentication

### API Key Format
- Format: `Bearer sc-{tenant}-{anything}`
- Examples:
  - `sc-test-local`
  - `sc-demo-123`
  - `sc-production-abc`

### Setting API Key in Frontend
1. Navigate to Settings (usually in the header/navigation)
2. Enter your API key
3. The key is stored in browser localStorage
4. All API requests will use this key automatically

### Setting API Key for API Calls
Include in the `Authorization` header:
```
Authorization: Bearer sc-test-local
```

## 📊 Monitoring & Debugging

### Backend Logs
- **Location:** `backend/logs/`
- **Files:**
  - `access.log` - All API requests
  - `errors.log` - Error messages
  - `semantic_ops.log` - Cache operations

### View Logs
```bash
# Windows PowerShell
Get-Content backend\logs\access.log -Tail 20
Get-Content backend\logs\semantic_ops.log -Tail 20

# Linux/Mac
tail -f backend/logs/access.log
tail -f backend/logs/semantic_ops.log
```

### Metrics Endpoint
- **URL:** http://localhost:8000/metrics
- **Returns:** Real-time cache performance metrics
- **Requires:** Authentication (Bearer token)

### Events Endpoint
- **URL:** http://localhost:8000/events?limit=100
- **Returns:** Recent cache events
- **Requires:** Authentication (Bearer token)

## 🧪 Testing the Application

### Test Script
Run the comprehensive test suite:
```bash
python test_caching_algorithm.py
```

### Manual Testing
1. **Start Backend:**
   ```bash
   cd backend
   python semantic_cache_server.py
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test in Browser:**
   - Open http://localhost:5173
   - Set API key
   - Make a query in the playground
   - Check metrics dashboard
   - View events/logs

## 🐛 Troubleshooting

### Frontend Not Loading
1. Check if frontend is running:
   ```bash
   cd frontend
   npm run dev
   ```
2. Check the port (may be different if 5173 is busy)
3. Check browser console for errors

### Backend Not Responding
1. Check if backend is running:
   ```bash
   curl http://localhost:8000/health
   ```
2. Check backend logs:
   ```bash
   Get-Content backend\logs\errors.log -Tail 20
   ```

### API Key Issues
1. Make sure API key format is correct: `sc-{tenant}-{anything}`
2. Include `Bearer` prefix in Authorization header
3. Check frontend localStorage for stored key

### CORS Issues
- Backend has CORS enabled for `http://localhost:5173`
- If using different port, update CORS settings in `backend/semantic_cache_server.py`

## 📝 Quick Reference

### URLs
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

### Commands
```bash
# Start Backend
cd backend
python semantic_cache_server.py

# Start Frontend
cd frontend
npm run dev

# Run Tests
python test_caching_algorithm.py
```

### API Key Examples
- `sc-test-local`
- `sc-demo-123`
- `sc-production-abc`

## 🎯 Next Steps

1. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Open Browser:**
   - Navigate to http://localhost:5173

3. **Set API Key:**
   - Use format: `sc-test-local`

4. **Test Application:**
   - Try queries in playground
   - Check metrics dashboard
   - View events/logs

5. **Explore API:**
   - Visit http://localhost:8000/docs
   - Try endpoints interactively

---

**Need Help?** Check the logs in `backend/logs/` or review the API documentation at http://localhost:8000/docs

