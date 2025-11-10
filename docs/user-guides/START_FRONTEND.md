# 🚀 How to Start the Frontend Application

## The Issue
You're seeing `ERR_CONNECTION_REFUSED` on `localhost:5173` because the **frontend development server is not running**.

## ✅ Solution: Start the Frontend

### Step 1: Open a New Terminal
Open a **new terminal window** (keep the backend running in its current terminal).

### Step 2: Navigate to Frontend Directory
```bash
cd frontend
```

### Step 3: Start the Development Server
```bash
npm run dev
```

### Step 4: Wait for Server to Start
You should see output like:
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 5: Open in Browser
1. Copy the URL shown (usually `http://localhost:5173`)
2. Open it in your browser
3. You should see the Semantis AI dashboard!

## 📍 Quick Reference

### Backend (Already Running)
- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs ✅ (You can see this)
- **Status:** ✅ Running

### Frontend (Needs to be Started)
- **URL:** http://localhost:5173
- **Command:** `cd frontend && npm run dev`
- **Status:** ❌ Not running (that's why you see the error)

## 🔍 What You're Seeing

### ✅ Backend is Working
- You can access http://localhost:8000/docs (Swagger UI)
- The backend API is running correctly

### ❌ Frontend is Not Running
- `localhost:5173` shows `ERR_CONNECTION_REFUSED`
- This means the frontend dev server hasn't been started

### ℹ️ About `localhost:8000` Showing "Not Found"
- This is **normal** - the backend API doesn't have a root endpoint (`/`)
- The backend is for API calls, not a web page
- Use http://localhost:8000/docs for the API documentation
- Use http://localhost:5173 for the frontend dashboard (once started)

## 🎯 Complete Setup

### Terminal 1: Backend (Already Running)
```bash
cd backend
python semantic_cache_server.py
```
✅ This is already running

### Terminal 2: Frontend (Start This Now)
```bash
cd frontend
npm run dev
```
❌ You need to start this

## 🚨 Troubleshooting

### If Port 5173 is Already in Use
- Vite will automatically use the next available port (5174, 5175, etc.)
- Check the terminal output for the actual URL
- The URL will be shown in the terminal when the server starts

### If `npm run dev` Fails
```bash
# Make sure you're in the frontend directory
cd frontend

# Install dependencies if needed
npm install

# Then start the server
npm run dev
```

### If You See "Command Not Found"
- Make sure Node.js and npm are installed
- Check: `node --version` and `npm --version`

## ✅ Once Started

After starting the frontend, you should be able to:

1. **Access the Dashboard:**
   - Open http://localhost:5173 in your browser
   - You'll see the Semantis AI interface

2. **Set API Key:**
   - Look for API key settings in the frontend
   - Enter: `sc-test-local` (or any key in format `sc-{tenant}-{anything}`)

3. **Use the Application:**
   - **Playground:** Test queries and see cache behavior
   - **Metrics:** View performance statistics
   - **Events:** See cache decisions
   - **Docs:** Read API documentation

## 📊 Summary

| Component | URL | Status | Action |
|-----------|-----|--------|--------|
| Backend API | http://localhost:8000 | ✅ Running | Already started |
| API Docs | http://localhost:8000/docs | ✅ Working | Accessible |
| Frontend | http://localhost:5173 | ❌ Not running | **Start with `npm run dev`** |

## 🎉 Next Steps

1. **Open a new terminal**
2. **Run:** `cd frontend && npm run dev`
3. **Wait for:** "ready in xxx ms" message
4. **Open:** http://localhost:5173 in your browser
5. **Enjoy:** Your application is now running!

---

**The backend is working perfectly!** You just need to start the frontend server in a separate terminal. Once both are running, you'll have the full application accessible in your browser.

