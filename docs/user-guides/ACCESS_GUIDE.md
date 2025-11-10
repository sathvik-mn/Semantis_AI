# 🚀 Complete Access Guide - Frontend, Backend & API Keys

## 📍 Where to Access Everything

### 1. Backend API

**Main URL:**
- **http://localhost:8000**

**API Documentation (Interactive):**
- **http://localhost:8000/docs** (Swagger UI - Try endpoints here!)

**Alternative Docs:**
- **http://localhost:8000/redoc** (ReDoc - Clean documentation)

**Health Check:**
- **http://localhost:8000/health**

**OpenAPI Specification:**
- **http://localhost:8000/openapi.json**

### 2. Frontend Dashboard

**Main URL:**
- **http://localhost:3000** (or check ports 3001-3003, 5173-5176)

**If Frontend is Not Running:**
```bash
cd frontend
npm run dev
```
Then check the terminal output for the actual URL (usually http://localhost:5173 or next available port)

## 🔑 API Keys

### View Generated API Keys

**Option 1: List Saved Keys**
```bash
cd backend
python api_key_generator.py --list
```

**Option 2: Check api_keys.json File**
```bash
cd backend
cat api_keys.json  # Linux/Mac
type api_keys.json  # Windows
```

### Generate New API Keys

**For a User:**
```bash
cd backend
python api_key_generator.py --tenant user123 --save
```

**For a Company:**
```bash
python api_key_generator.py --tenant company-abc --save
```

**Generate Multiple Keys:**
```bash
python api_key_generator.py --tenant user123 --count 5 --save
```

### Example API Keys (From Generated Keys)

**Tenant: company-abc**
- `sc-company-abc-tMlyiL05Af6VjlXE`
- `sc-company-abc-1CfNTnugLK4Wuva1`

**Tenant: user123**
- `sc-user123-IZFZE7AggilUPz3V`
- `sc-user123-hArQMPJVhlDpYzel`
- `sc-user123-CDjCTJeMGPb21SLD`

**Test Key (Always Available):**
- `sc-test-local`

## 🎯 How to Enter API Keys in Frontend

### Step 1: Open Frontend Dashboard
1. Navigate to: **http://localhost:3000** (or your frontend URL)
2. You should see the Semantis AI dashboard

### Step 2: Find API Key Settings
The API key input is typically located in one of these places:

**Option A: Settings Page**
1. Look for a "Settings" link in the navigation menu
2. Click on "Settings"
3. Find the "API Key" field
4. Enter your API key (e.g., `sc-user123-IZFZE7AggilUPz3V`)
5. Click "Save" or "Update"

**Option B: Header/Navigation Bar**
1. Look for a gear icon (⚙️) or "Settings" in the top navigation
2. Click on it
3. Enter your API key
4. Save

**Option C: On First Use**
1. When you first try to use a feature (like Playground)
2. You may be prompted to enter an API key
3. Enter your key and save

### Step 3: Verify API Key is Set
1. Try making a query in the Playground
2. If it works, your API key is set correctly
3. If you get an error, check the key format

## 📝 API Key Format

**Format:** `sc-{tenant}-{random_string}`

**Examples:**
- `sc-user123-IZFZE7AggilUPz3V`
- `sc-company-abc-tMlyiL05Af6VjlXE`
- `sc-test-local`

**Important:**
- Must start with `sc-`
- Tenant name can contain letters, numbers, dashes, underscores
- Random string is generated automatically

## 🔍 Quick Access Checklist

### Backend
- [ ] Backend running? Check: http://localhost:8000/health
- [ ] API Docs accessible? Check: http://localhost:8000/docs
- [ ] Can test endpoints? Use Swagger UI at /docs

### Frontend
- [ ] Frontend running? Check: http://localhost:3000 (or other ports)
- [ ] Dashboard loads? Should see Semantis AI interface
- [ ] API key entered? Check Settings page

### API Keys
- [ ] Keys generated? Run: `python api_key_generator.py --list`
- [ ] Key format correct? Should be: `sc-{tenant}-{random}`
- [ ] Key saved in frontend? Check localStorage or Settings

## 🚀 Quick Start Steps

### 1. Start Backend (if not running)
```bash
cd backend
python semantic_cache_server.py
```
✅ Backend available at: http://localhost:8000

### 2. Start Frontend (if not running)
```bash
cd frontend
npm run dev
```
✅ Frontend available at: http://localhost:5173 (or shown URL)

### 3. Generate API Key
```bash
cd backend
python api_key_generator.py --tenant myuser --save
```
✅ Key generated: `sc-myuser-{random}`

### 4. Enter API Key in Frontend
1. Open frontend: http://localhost:3000 (or your URL)
2. Go to Settings
3. Enter API key: `sc-myuser-{random}`
4. Save

### 5. Test the Application
1. Go to Playground
2. Enter a query: "What is AI?"
3. Click Submit
4. See the response and cache status

## 📊 Testing API Keys

### Test in API Docs (Swagger)
1. Go to: http://localhost:8000/docs
2. Click "Authorize" button (top right)
3. Enter: `sc-user123-IZFZE7AggilUPz3V` (or your key)
4. Click "Authorize"
5. Try any endpoint (e.g., `/v1/chat/completions`)

### Test with curl
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sc-user123-IZFZE7AggilUPz3V" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Test in Frontend
1. Open frontend dashboard
2. Go to Playground
3. Enter a query
4. Click Submit
5. Should see response (if API key is set)

## 🐛 Troubleshooting

### Frontend Not Loading
```bash
# Check if frontend is running
cd frontend
npm run dev

# Check the URL shown in terminal
# Usually: http://localhost:5173
```

### API Key Not Working
1. **Check format:** Must be `sc-{tenant}-{random}`
2. **Check in frontend:** Settings → API Key field
3. **Check in browser:** Open DevTools → Application → LocalStorage → `semantic_api_key`
4. **Test in API docs:** http://localhost:8000/docs → Authorize

### Backend Not Responding
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not running, start it
cd backend
python semantic_cache_server.py
```

### Can't Find API Key Settings
1. Look for gear icon (⚙️) in navigation
2. Check top-right corner for user menu
3. Look for "Settings" or "Configuration" link
4. Check browser console for errors

## 📋 Summary

### URLs
- **Backend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000 (or check other ports)

### API Keys
- **Generate:** `python backend/api_key_generator.py --tenant yourname --save`
- **List:** `python backend/api_key_generator.py --list`
- **Format:** `sc-{tenant}-{random}`

### Enter API Key
1. Open frontend dashboard
2. Go to Settings
3. Enter API key
4. Save

### Test
1. Use Playground to test queries
2. Check metrics dashboard
3. View events/logs

---

**Need Help?**
- Check `API_KEY_MANAGEMENT.md` for detailed key management
- Check browser console for errors
- Verify backend is running: http://localhost:8000/health

