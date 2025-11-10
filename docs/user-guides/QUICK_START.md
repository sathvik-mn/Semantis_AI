# 🚀 Quick Start Guide - Access Your Application

## Where to Check Your Application

### 1. **Backend API** (FastAPI)
- **Main URL:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

### 2. **Frontend Dashboard** (React)
- **Main URL:** http://localhost:5173
- **Note:** Must be started manually (see below)

## 🎯 Quick Access Steps

### Step 1: Verify Backend is Running

Open your browser and go to:
```
http://localhost:8000/docs
```

You should see the **Swagger UI** with all API endpoints.

### Step 2: Start Frontend

Open a **new terminal** and run:

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

### Step 3: Access Frontend Dashboard

1. Copy the URL shown (usually `http://localhost:5173`)
2. Open it in your browser
3. You'll see the Semantis AI dashboard

### Step 4: Set API Key

1. In the frontend, find the API key settings
2. Enter: `sc-test-local` (or any key in format `sc-{tenant}-{anything}`)
3. Save the key

### Step 5: Use the Application!

- **Playground:** Test queries and see cache in action
- **Metrics:** View performance statistics
- **Events:** See cache decisions (exact/semantic/miss)
- **Docs:** Read API documentation

## 📍 All Access Points

### Backend Endpoints:
- **API Base:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Metrics:** http://localhost:8000/metrics (requires auth)
- **Events:** http://localhost:8000/events (requires auth)

### Frontend Pages:
- **Dashboard:** http://localhost:5173
- **Playground:** http://localhost:5173/playground
- **Metrics:** http://localhost:5173/metrics
- **Logs:** http://localhost:5173/logs
- **Docs:** http://localhost:5173/docs

## 🔍 Testing the Application

### Option 1: Use Frontend (Recommended)
1. Start frontend: `cd frontend && npm run dev`
2. Open http://localhost:5173
3. Set API key: `sc-test-local`
4. Go to Playground
5. Enter a query: "What is AI?"
6. See the response and cache status

### Option 2: Use API Docs (Interactive)
1. Open http://localhost:8000/docs
2. Click on an endpoint (e.g., `/v1/chat/completions`)
3. Click "Try it out"
4. Set Authorization: `Bearer sc-test-local`
5. Enter request body
6. Click "Execute"
7. See the response

### Option 3: Use curl/Postman
```bash
# Health check
curl http://localhost:8000/health

# Get metrics
curl -H "Authorization: Bearer sc-test-local" http://localhost:8000/metrics

# Chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sc-test-local" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"What is AI?"}]}'
```

## 🎨 Frontend Features

Once you access http://localhost:5173, you'll see:

1. **Home/Dashboard**
   - Overview of cache performance
   - Key metrics at a glance

2. **Playground** (`/playground`)
   - Interactive query testing
   - Real-time cache behavior
   - Response preview

3. **Metrics** (`/metrics`)
   - Detailed performance charts
   - Hit ratios
   - Latency statistics

4. **Logs/Events** (`/logs`)
   - Recent cache events
   - Filter by type
   - Export data

5. **Documentation** (`/docs`)
   - API usage guides
   - Code examples
   - Integration instructions

## 🔐 API Key Format

Use this format for API keys:
```
sc-{tenant}-{anything}
```

Examples:
- `sc-test-local`
- `sc-demo-123`
- `sc-production-abc`

## 🐛 Troubleshooting

### Backend Not Accessible
```bash
# Check if running
curl http://localhost:8000/health

# If not running, start it
cd backend
python semantic_cache_server.py
```

### Frontend Not Starting
```bash
# Make sure you're in frontend directory
cd frontend

# Install dependencies (if needed)
npm install

# Start dev server
npm run dev
```

### Port Already in Use
- Frontend will automatically use next available port
- Check the terminal output for the actual URL
- Backend port 8000 can be changed in `semantic_cache_server.py`

### API Key Not Working
- Make sure format is correct: `Bearer sc-test-local`
- Check Authorization header is included
- Verify backend is running and accepting requests

## 📊 Monitoring

### View Logs
```bash
# Access logs
tail -f backend/logs/access.log

# Error logs
tail -f backend/logs/errors.log

# Semantic operations
tail -f backend/logs/semantic_ops.log
```

### Check Metrics
- Frontend: http://localhost:5173/metrics
- API: http://localhost:8000/metrics (with auth)

## ✅ Quick Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Can access http://localhost:8000/docs
- [ ] Frontend started (`npm run dev` in frontend folder)
- [ ] Can access frontend dashboard (usually http://localhost:5173)
- [ ] API key set in frontend (`sc-test-local`)
- [ ] Can make queries in playground
- [ ] Can view metrics
- [ ] Can see events/logs

## 🎯 Next Steps

1. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Open Browser:**
   - Go to http://localhost:5173 (or URL shown in terminal)

3. **Set API Key:**
   - Use: `sc-test-local`

4. **Test Application:**
   - Try queries in playground
   - Check metrics dashboard
   - View events/logs

5. **Explore API:**
   - Visit http://localhost:8000/docs
   - Try endpoints interactively

---

**Need Help?** Check `HOW_TO_ACCESS_APPLICATION.md` for detailed instructions.

