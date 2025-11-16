# How to Access Admin Features

## Quick Start

### Step 1: Create Frontend Environment File

Create a `.env` file in the `frontend/` directory with:

```env
VITE_BACKEND_URL=http://localhost:8000
VITE_ADMIN_API_KEY=admin-secret-key-change-me
```

### Step 2: Restart Frontend

After creating the `.env` file, **restart your frontend dev server**:

```powershell
cd D:\Semantis_AI\frontend
# Stop current server (Ctrl+C if running)
npm run dev
```

**Important:** Vite requires a server restart to load `.env` variables.

### Step 3: Access Admin Dashboard

Open your browser and navigate to:

**http://localhost:3000/admin**

You should see the admin dashboard with:
- Dashboard (overview)
- Users (user management)
- Top Users (leaderboard)
- Analytics (detailed analytics)
- Settings (system settings)

---

## Direct URLs

- **Admin Dashboard:** http://localhost:3000/admin
- **Admin Users:** http://localhost:3000/admin/users
- **Admin Top Users:** http://localhost:3000/admin/top-users
- **Admin Analytics:** http://localhost:3000/admin/analytics
- **Admin Settings:** http://localhost:3000/admin/settings

---

## Test Admin API Directly

You can test the admin API directly using curl or Python:

```powershell
# Test admin summary endpoint
curl "http://localhost:8000/admin/summary?api_key=admin-secret-key-change-me"
```

Or using Python:

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

### If admin page shows errors:

1. **Check `.env` file exists** in `frontend/` directory
2. **Verify `VITE_ADMIN_API_KEY` is set** to `admin-secret-key-change-me`
3. **Restart frontend server** (Vite needs restart for env changes)
4. **Check browser console** for API errors (F12 → Console)

### If you see 401 Unauthorized:

- Make sure `VITE_ADMIN_API_KEY` matches the backend default: `admin-secret-key-change-me`
- Check backend is running on port 8000

### If admin routes don't load:

- Navigate to `/admin` (not `/admin/`)
- Check browser console for routing errors
- Verify frontend is running on port 3000

---

## Default Admin API Key

The default admin API key is: **`admin-secret-key-change-me`**

This can be changed by setting the `ADMIN_API_KEY` environment variable on the backend, and updating `VITE_ADMIN_API_KEY` in the frontend `.env` file.

---

## Summary

1. ✅ Create `.env` file in `frontend/` with admin API key
2. ✅ Restart frontend dev server
3. ✅ Navigate to http://localhost:3000/admin
4. ✅ Admin dashboard should load with data

**See `ADMIN_ACCESS_GUIDE.md` for detailed documentation.**


