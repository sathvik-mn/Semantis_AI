# Admin Dashboard Access Guide

## How to Access Admin Features

The admin dashboard is available at **http://localhost:3000/admin** but requires proper configuration.

### Step 1: Set Admin API Key

The frontend needs the admin API key to authenticate with the backend admin API.

1. **Create/Update `.env` file in the frontend directory:**

```bash
# In frontend/.env
VITE_BACKEND_URL=http://localhost:8000
VITE_ADMIN_API_KEY=admin-secret-key-change-me
```

**Default Admin API Key:** `admin-secret-key-change-me`

### Step 2: Restart Frontend Dev Server

After setting the environment variable, restart the frontend:

```powershell
cd D:\Semantis_AI\frontend
# Stop current server (Ctrl+C)
npm run dev
```

**Important:** Vite requires a restart to pick up `.env` file changes.

### Step 3: Access Admin Dashboard

Navigate to: **http://localhost:3000/admin**

Available pages:
- **Dashboard** - `/admin` - Overview with KPIs and charts
- **Users** - `/admin/users` - User management
- **Top Users** - `/admin/top-users` - Leaderboard
- **Analytics** - `/admin/analytics` - Detailed analytics
- **Settings** - `/admin/settings` - System settings

---

## Admin API Endpoints

The backend admin API is available at: **http://localhost:8000/admin**

All endpoints require the `api_key` query parameter:

```
http://localhost:8000/admin/summary?api_key=admin-secret-key-change-me
```

### Available Endpoints:

1. **GET** `/admin/summary` - Analytics summary
2. **GET** `/admin/users` - List all users
3. **GET** `/admin/users/{tenant_id}` - User details
4. **PATCH** `/admin/users/{tenant_id}/status` - Update user status
5. **PATCH** `/admin/users/{tenant_id}/plan` - Update user plan
6. **GET** `/admin/top-users` - Top users leaderboard
7. **GET** `/admin/analytics/growth` - Growth analytics
8. **GET** `/admin/analytics/usage` - Usage analytics
9. **GET** `/admin/analytics/plans` - Plan distribution
10. **GET** `/admin/system/health` - System health

---

## Quick Test

### Test Admin API Directly:

```powershell
# Test admin summary endpoint
curl "http://localhost:8000/admin/summary?api_key=admin-secret-key-change-me"
```

### Or using Python:

```python
import requests

response = requests.get(
    "http://localhost:8000/admin/summary",
    params={"api_key": "admin-secret-key-change-me"}
)
print(response.json())
```

---

## Troubleshooting

### Issue: Admin dashboard shows errors/empty data

**Solution:**
1. Check that `.env` file exists in `frontend/` directory
2. Verify `VITE_ADMIN_API_KEY` is set correctly
3. Restart the frontend dev server
4. Check browser console for API errors

### Issue: 401 Unauthorized errors

**Solution:**
1. Verify admin API key matches between frontend and backend
2. Default key is: `admin-secret-key-change-me`
3. Check backend logs for authentication errors

### Issue: Cannot see admin routes

**Solution:**
1. Make sure you're accessing `/admin` (not `/admin/`)
2. Check that routes are configured in `App.tsx`
3. Verify `AdminLayout` component is loading

---

## Security Note

**Important:** Change the default admin API key in production!

1. **Backend:** Set environment variable:
   ```bash
   $env:ADMIN_API_KEY="your-secure-key-here"
   ```

2. **Frontend:** Update `.env` file:
   ```
   VITE_ADMIN_API_KEY=your-secure-key-here
   ```

---

## Current Configuration

- **Backend Admin API:** http://localhost:8000/admin
- **Frontend Admin:** http://localhost:3000/admin
- **Default Admin Key:** `admin-secret-key-change-me`
- **Environment Variable:** `ADMIN_API_KEY` (backend), `VITE_ADMIN_API_KEY` (frontend)

---

**Need Help?** Check browser console and network tab for detailed error messages.


