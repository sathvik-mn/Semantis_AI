# Fix: API Key Generation 404 Error

## Issue

The `/api/keys/generate` endpoint is returning **404 Not Found** when called from the frontend.

**From logs:**
```
2025-11-16T12:15:07 | INFO | RESP | POST /api/keys/generate | status=404 | time=12.48ms
```

## Root Cause

The backend server was running **before** the endpoint was added, so it doesn't know about the new route. The endpoint exists in the code but isn't registered in the running server instance.

## Solution

**Restart the backend server** to load the new endpoint:

### Step 1: Stop the Backend Server

Press `Ctrl+C` in the terminal where the backend is running, or:

```powershell
# Find and stop Python backend process
Get-Process python | Where-Object {$_.Path -like "*python*"} | Stop-Process -Force
```

### Step 2: Start the Backend Server

```powershell
cd D:\Semantis_AI\backend
python semantic_cache_server.py
```

Or if using uvicorn directly:
```powershell
cd D:\Semantis_AI\backend
uvicorn semantic_cache_server:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Verify the Endpoint

After restarting, the endpoint should work. You can verify:

1. **Check the logs** - Should see "Admin routes registered" message
2. **Test the endpoint** - The frontend "Generate API Key" button should work
3. **Check OpenAPI docs** - Visit http://localhost:8000/docs and look for `/api/keys/generate`

## Verification

After restart, the endpoint should return **200 OK** instead of **404**.

**Expected Response:**
```json
{
  "api_key": "sc-usr_xxxxx-XXXX-XXXX-XXXX",
  "tenant_id": "usr_xxxxx",
  "plan": "free",
  "created_at": "2025-11-16T12:16:17",
  "format": "Bearer sc-usr_xxxxx-XXXX-XXXX-XXXX",
  "message": "API key generated successfully. Save this key securely - it won't be shown again."
}
```

---

**Note:** When using `--reload` flag with uvicorn, the server will automatically reload when files change, so you won't need to manually restart in the future.

