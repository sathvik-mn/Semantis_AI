# 🚀 Quick Access Guide - All URLs & API Keys

## 📍 Access URLs

### Backend API
- **Main URL:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs (Interactive Swagger UI)
- **Health Check:** http://localhost:8000/health
- **OpenAPI Spec:** http://localhost:8000/openapi.json

### Frontend Dashboard
- **Main URL:** http://localhost:3001 (or check 3000, 3002, 3003, 5173)
- **Status:** ✅ Running

## 🔑 Available API Keys

### Saved API Keys

**Tenant: company-abc**
- `sc-company-abc-tMlyiL05Af6VjlXE`
- `sc-company-abc-1CfNTnugLK4Wuva1`

**Tenant: demo-user**
- `sc-demo-user-VFcWBpkaiINmSl41`

**Test Key (Always Available)**
- `sc-test-local`

### Generate New API Keys

```bash
cd backend
python api_key_generator.py --tenant your-tenant-name --save
```

**Example:**
```bash
python api_key_generator.py --tenant user123 --save
# Output: sc-user123-{random_string}
```

## 🎯 How to Enter API Key in Frontend

### Step-by-Step Instructions

1. **Open Frontend Dashboard**
   - Navigate to: **http://localhost:3001**
   - You should see the Semantis AI dashboard

2. **Find API Key Settings**
   - Look for a **Settings** icon (⚙️) or link in the navigation
   - Or look for **API Key** input field
   - It might be in the header, sidebar, or a settings page

3. **Enter API Key**
   - Copy one of the API keys above (e.g., `sc-demo-user-VFcWBpkaiINmSl41`)
   - Paste it into the API Key field
   - Click **Save** or **Update**

4. **Verify API Key is Set**
   - Try using the Playground to make a query
   - If it works, your API key is set correctly!
   - If you get an error, check the key format

### Alternative: Check Browser Storage

1. Open browser DevTools (F12)
2. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Click on **Local Storage** → `http://localhost:3001`
4. Look for key: `semantic_api_key`
5. Value should be your API key (e.g., `sc-demo-user-VFcWBpkaiINmSl41`)

## 🔍 Testing API Keys

### Option 1: Test in Frontend Playground
1. Open: http://localhost:3001
2. Go to **Playground** page
3. Enter a query: "What is AI?"
4. Click Submit
5. Should see response (if API key is set)

### Option 2: Test in API Docs (Swagger)
1. Open: http://localhost:8000/docs
2. Click **Authorize** button (top right, green button with lock icon)
3. Enter API key: `sc-demo-user-VFcWBpkaiINmSl41`
4. Click **Authorize**
5. Try any endpoint (e.g., `/v1/chat/completions`)
6. Click **Try it out**
7. Enter request body and click **Execute**

### Option 3: Test with curl
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sc-demo-user-VFcWBpkaiINmSl41" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## 📋 Quick Reference

### Backend Endpoints
- **Health:** http://localhost:8000/health
- **Metrics:** http://localhost:8000/metrics (requires auth)
- **Events:** http://localhost:8000/events (requires auth)
- **Chat:** http://localhost:8000/v1/chat/completions (requires auth)
- **Query:** http://localhost:8000/query?prompt=Hello (requires auth)

### Frontend Pages
- **Dashboard:** http://localhost:3001
- **Playground:** http://localhost:3001/playground
- **Metrics:** http://localhost:3001/metrics
- **Logs:** http://localhost:3001/logs
- **Docs:** http://localhost:3001/docs

### API Key Format
- **Format:** `sc-{tenant}-{random_string}`
- **Example:** `sc-demo-user-VFcWBpkaiINmSl41`
- **Usage:** `Authorization: Bearer sc-demo-user-VFcWBpkaiINmSl41`

## 🚀 Quick Start

### 1. Access Backend
```
http://localhost:8000/docs
```
✅ Interactive API documentation

### 2. Access Frontend
```
http://localhost:3001
```
✅ Dashboard interface

### 3. Use API Key
- **In Frontend:** Settings → API Key → Enter key → Save
- **In API Docs:** Click Authorize → Enter key → Authorize
- **In Code:** `Authorization: Bearer sc-demo-user-VFcWBpkaiINmSl41`

## 🐛 Troubleshooting

### Frontend Not Loading?
```bash
cd frontend
npm run dev
```
Check terminal for the URL (usually http://localhost:5173)

### API Key Not Working?
1. Check format: Must be `sc-{tenant}-{random}`
2. Check in frontend: Settings → API Key
3. Check in browser: DevTools → Application → LocalStorage
4. Test in API docs: http://localhost:8000/docs → Authorize

### Backend Not Responding?
```bash
cd backend
python semantic_cache_server.py
```
Check: http://localhost:8000/health

## 📝 Summary

| Item | URL/Value |
|------|-----------|
| **Backend** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Frontend** | http://localhost:3001 |
| **API Key 1** | `sc-company-abc-tMlyiL05Af6VjlXE` |
| **API Key 2** | `sc-company-abc-1CfNTnugLK4Wuva1` |
| **API Key 3** | `sc-demo-user-VFcWBpkaiINmSl41` |
| **Test Key** | `sc-test-local` |

---

**Ready to use!** 🎉

1. Open frontend: http://localhost:3001
2. Enter API key in Settings
3. Start using the application!

