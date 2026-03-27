# 🚀 Complete Access Guide - Frontend, Backend & API Keys

## 📍 Access URLs

### ✅ Backend API
- **URL:** http://localhost:8000
- **API Documentation (Swagger):** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Status:** ✅ Running

### ✅ Frontend Dashboard
- **URL:** http://localhost:3001
- **Status:** ✅ Running
- **Note:** If not accessible, check ports 3000, 3002, 3003, or 5173

## 🔑 Available API Keys

### Saved API Keys (Ready to Use)

**1. Tenant: company-abc**
- `sc-company-abc-tMlyiL05Af6VjlXE`
- `sc-company-abc-1CfNTnugLK4Wuva1`

**2. Tenant: demo-user**
- `sc-demo-user-VFcWBpkaiINmSl41`

**3. Test Key (Always Available)**
- `sc-test-local`

### Generate More API Keys

```bash
cd backend
python api_key_generator.py --tenant your-tenant-name --save
```

**Examples:**
```bash
# For a user
python api_key_generator.py --tenant user123 --save

# For a company
python api_key_generator.py --tenant my-company --save

# Generate multiple keys
python api_key_generator.py --tenant user123 --count 5 --save
```

## 🎯 How to Enter API Key in Frontend

### Method 1: Landing Page (First Time)

1. **Open Frontend**
   - Navigate to: **http://localhost:3001**
   - You'll see the landing page with an API key input field

2. **Enter API Key**
   - Copy one of the API keys above (e.g., `sc-demo-user-VFcWBpkaiINmSl41`)
   - Paste it into the "API Key" input field
   - Click **"Get Started"** or **"Submit"** button

3. **Access Dashboard**
   - After entering a valid API key, you'll be redirected to the dashboard
   - You can now use all features (Playground, Metrics, Logs, etc.)

### Method 2: Settings Page (Change API Key)

1. **Open Frontend**
   - Navigate to: **http://localhost:3001**

2. **Go to Settings**
   - Click on **"Settings"** in the navigation menu
   - Or navigate to: **http://localhost:3001/settings**

3. **Update API Key**
   - Find the API Key input field
   - Enter your new API key
   - Click **"Save"** or **"Update"**

4. **Verify**
   - Try using the Playground to verify the key works
   - Or check the Metrics page to see your tenant's data

### Method 3: Browser LocalStorage (Advanced)

1. **Open Browser DevTools**
   - Press `F12` or `Right-click → Inspect`

2. **Go to Application Tab**
   - Click on **"Application"** (Chrome) or **"Storage"** (Firefox)

3. **Check Local Storage**
   - Expand **"Local Storage"** → `http://localhost:3001`
   - Look for key: `semantic_api_key`
   - Value should be your API key

4. **Manually Set (if needed)**
   - Right-click on `semantic_api_key`
   - Select **"Edit"** or **"Delete"**
   - Add/Update the value with your API key

## 🔍 Testing API Keys

### Test 1: Frontend Playground
1. Open: http://localhost:3001
2. Enter API key (if not set)
3. Go to **Playground** page
4. Enter query: "What is AI?"
5. Click Submit
6. ✅ Should see response (if API key is valid)

### Test 2: API Documentation (Swagger)
1. Open: http://localhost:8000/docs
2. Click **"Authorize"** button (top right, green button with 🔒)
3. Enter API key: `sc-demo-user-VFcWBpkaiINmSl41`
4. Click **"Authorize"**
5. Try endpoint: `/v1/chat/completions`
6. Click **"Try it out"**
7. Enter request body:
   ```json
   {
     "model": "gpt-4o-mini",
     "messages": [{"role": "user", "content": "Hello"}]
   }
   ```
8. Click **"Execute"**
9. ✅ Should see response (if API key is valid)

### Test 3: curl Command
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sc-demo-user-VFcWBpkaiINmSl41" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## 📋 Complete URL List

### Backend Endpoints
- **Base URL:** http://localhost:8000
- **Health:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs
- **Metrics:** http://localhost:8000/metrics (requires auth)
- **Events:** http://localhost:8000/events (requires auth)
- **Chat:** http://localhost:8000/v1/chat/completions (requires auth)
- **Query:** http://localhost:8000/query?prompt=Hello (requires auth)

### Frontend Pages
- **Landing Page:** http://localhost:3001/
- **Dashboard/Playground:** http://localhost:3001/playground
- **Metrics:** http://localhost:3001/metrics
- **Logs/Events:** http://localhost:3001/logs
- **Settings:** http://localhost:3001/settings
- **Documentation:** http://localhost:3001/docs

## 🚀 Quick Start Guide

### Step 1: Access Frontend
```
Open: http://localhost:3001
```
You'll see the landing page with API key input

### Step 2: Enter API Key
```
Use one of these keys:
- sc-demo-user-VFcWBpkaiINmSl41
- sc-company-abc-tMlyiL05Af6VjlXE
- sc-test-local
```

### Step 3: Start Using
- Click **"Get Started"** after entering API key
- You'll be redirected to the dashboard
- Use Playground to test queries
- Check Metrics for performance stats
- View Logs for cache events

## 📝 API Key Format

**Format:** `sc-{tenant}-{random_string}`

**Examples:**
- `sc-demo-user-VFcWBpkaiINmSl41`
- `sc-company-abc-tMlyiL05Af6VjlXE`
- `sc-test-local`

**Rules:**
- Must start with `sc-`
- Tenant can contain: letters, numbers, dashes, underscores
- Random string is auto-generated (16+ characters recommended)

## 🎯 Frontend Features

### 1. Landing Page (`/`)
- Enter API key for first time
- Get started with the application

### 2. Playground (`/playground`)
- Test LLM queries
- See cache hits/misses in real-time
- View response times

### 3. Metrics (`/metrics`)
- View cache performance
- Hit ratios (exact + semantic)
- Latency statistics
- Token savings

### 4. Logs (`/logs`)
- Recent cache events
- Filter by type (exact/semantic/miss)
- Download as CSV

### 5. Settings (`/settings`)
- Update API key
- Configure cache settings
- View current settings

### 6. Documentation (`/docs`)
- API usage guides
- Code examples
- Integration instructions

## 🔒 Security Notes

### API Key Storage
- API keys are stored in browser **LocalStorage**
- Keys are **never** transmitted except in API request headers
- Each tenant has **isolated** cache data

### Best Practices
- ✅ Use different keys for different users/tenants
- ✅ Don't share API keys publicly
- ✅ Rotate keys periodically
- ✅ Monitor key usage

## 🐛 Troubleshooting

### Frontend Not Loading?
```bash
cd frontend
npm run dev
```
Check terminal for the actual URL

### API Key Not Working?
1. **Check format:** Must be `sc-{tenant}-{random}`
2. **Check in frontend:** Landing page or Settings
3. **Check in browser:** DevTools → Application → LocalStorage
4. **Test in API docs:** http://localhost:8000/docs → Authorize

### Can't Enter API Key?
1. **Clear browser cache:** Clear LocalStorage
2. **Check console:** Open DevTools → Console for errors
3. **Try different browser:** Sometimes cache issues
4. **Check URL:** Make sure you're on http://localhost:3001

### Backend Not Responding?
```bash
cd backend
python semantic_cache_server.py
```
Check: http://localhost:8000/health

## 📊 Summary Table

| Item | URL/Value |
|------|-----------|
| **Backend** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Frontend** | http://localhost:3001 |
| **Landing Page** | http://localhost:3001/ |
| **Playground** | http://localhost:3001/playground |
| **Settings** | http://localhost:3001/settings |
| **API Key 1** | `sc-demo-user-VFcWBpkaiINmSl41` |
| **API Key 2** | `sc-company-abc-tMlyiL05Af6VjlXE` |
| **API Key 3** | `sc-company-abc-1CfNTnugLK4Wuva1` |
| **Test Key** | `sc-test-local` |

## ✅ Quick Checklist

### Backend
- [x] Running on http://localhost:8000
- [x] API docs accessible at /docs
- [x] Health check passing

### Frontend
- [x] Running on http://localhost:3001
- [ ] API key entered (you need to do this)
- [ ] Dashboard accessible

### API Keys
- [x] Keys generated and saved
- [x] Keys ready to use
- [ ] Key entered in frontend (you need to do this)

## 🎉 Ready to Use!

1. **Open Frontend:** http://localhost:3001
2. **Enter API Key:** Use `sc-demo-user-VFcWBpkaiINmSl41` or any key above
3. **Click Get Started**
4. **Start Using:** Playground, Metrics, Logs, etc.

---

**Need More Help?**
- Check `ACCESS_GUIDE.md` for detailed instructions
- Check `API_KEY_MANAGEMENT.md` for key management
- Check browser console for errors
- Verify backend is running: http://localhost:8000/health

