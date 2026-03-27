# 🔌 Plug and Play Guide - Quick Verification

## 🚀 Quick Start Checklist

### 1. Check Backend is Running
```bash
# Check if server is running
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","service":"semantic-cache","version":"0.1.0"}
```

### 2. Check Frontend is Running
```bash
# Open in browser
http://localhost:3001
# or
http://localhost:5173
```

### 3. Quick API Test
```bash
# Test with a simple query
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sc-test-local" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "what is AI?"}]
  }'
```

## 📋 Complete Verification Steps

### Step 1: Backend Health Check
```bash
cd backend
python -c "import requests; r = requests.get('http://localhost:8000/health'); print(r.json())"
```

**Expected:** `{"status":"ok","service":"semantic-cache","version":"0.1.0"}`

### Step 2: Test Cache Behavior
```bash
cd backend
python test_api.py
```

**Expected:**
- ✅ Health check passes
- ✅ Metrics endpoint works
- ✅ Cache miss on first query
- ✅ Cache hit on second query

### Step 3: Test Typo Matching
```bash
cd backend
python test_fresh_typo.py
```

**Expected:**
- ✅ First query: MISS
- ✅ Second query: SEMANTIC HIT (similarity ~0.80)

### Step 4: Check Database
```bash
cd backend
python api_key_generator.py --list
```

**Expected:** List of API keys with plans

### Step 5: Test Frontend
1. Open browser: `http://localhost:3001`
2. Enter API key: `sc-test-local` (or any key from `--list`)
3. Enter query: "what is AI?"
4. Check if response appears

## 🧪 Automated Test Suite

### Run All Tests
```bash
cd backend

# 1. Basic API tests
python test_api.py

# 2. Typo matching tests
python test_fresh_typo.py

# 3. Similarity check
python check_typo_similarity.py
```

## 🔍 Verification Checklist

### Backend ✅
- [ ] Server running on port 8000
- [ ] Health endpoint responds
- [ ] API endpoints work
- [ ] Cache persistence works
- [ ] Database initialized

### Frontend ✅
- [ ] Dev server running
- [ ] Can access dashboard
- [ ] Can enter API key
- [ ] Can make queries
- [ ] Metrics display correctly

### Cache ✅
- [ ] Cache saves to disk
- [ ] Cache loads on startup
- [ ] Semantic matching works
- [ ] Typo tolerance works

### Database ✅
- [ ] Database file exists
- [ ] Can list API keys
- [ ] Can create new keys
- [ ] Usage tracking works

## 🛠️ Troubleshooting

### Backend Not Running
```bash
cd backend
python semantic_cache_server.py
```

### Frontend Not Running
```bash
cd frontend
npm run dev
```

### Cache Issues
```bash
# Clear cache
rm backend/cache_data/cache.pkl

# Restart server
python backend/semantic_cache_server.py
```

### Database Issues
```bash
# Reinitialize database
cd backend
python -c "from database import init_database; init_database()"
```

## 📊 Quick Status Check

### One-Line Status
```bash
# Backend
curl http://localhost:8000/health && echo "✅ Backend OK" || echo "❌ Backend DOWN"

# Frontend
curl http://localhost:3001 && echo "✅ Frontend OK" || echo "❌ Frontend DOWN"
```

### Detailed Status
```bash
cd backend
python -c "
import requests
import sys

# Check backend
try:
    r = requests.get('http://localhost:8000/health', timeout=2)
    print('✅ Backend: OK' if r.status_code == 200 else '❌ Backend: ERROR')
except:
    print('❌ Backend: DOWN')

# Check frontend
try:
    r = requests.get('http://localhost:3001', timeout=2)
    print('✅ Frontend: OK' if r.status_code == 200 else '❌ Frontend: ERROR')
except:
    print('❌ Frontend: DOWN')
"
```

## 🎯 Quick Test Script

Create `quick_test.py`:
```python
import requests
import sys

BASE_URL = "http://localhost:8000"
API_KEY = "Bearer sc-test-local"

def test():
    print("=" * 60)
    print("Quick Plug and Play Test")
    print("=" * 60)
    
    # 1. Health check
    print("\n1. Health Check...")
    try:
        r = requests.get(f"{BASE_URL}/health")
        if r.status_code == 200:
            print("   ✅ Backend is running")
        else:
            print(f"   ❌ Backend returned {r.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend is down: {e}")
        return False
    
    # 2. Test query
    print("\n2. Test Query...")
    try:
        r = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={"Authorization": API_KEY, "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hello"}]}
        )
        if r.status_code == 200:
            result = r.json()
            print("   ✅ Query successful")
            print(f"   Response: {result['choices'][0]['message']['content'][:50]}...")
        else:
            print(f"   ❌ Query failed: {r.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Query error: {e}")
        return False
    
    # 3. Test metrics
    print("\n3. Metrics Check...")
    try:
        r = requests.get(f"{BASE_URL}/metrics", headers={"Authorization": API_KEY})
        if r.status_code == 200:
            metrics = r.json()
            print("   ✅ Metrics retrieved")
            print(f"   Cache entries: {metrics.get('entries', 0)}")
        else:
            print(f"   ❌ Metrics failed: {r.status_code}")
    except Exception as e:
        print(f"   ❌ Metrics error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test()
    sys.exit(0 if success else 1)
```

Run it:
```bash
cd backend
python quick_test.py
```

## 🎉 Success Indicators

### Backend Working
- ✅ Health endpoint responds
- ✅ Can make API calls
- ✅ Cache works (miss → hit)
- ✅ Metrics show data

### Frontend Working
- ✅ Dashboard loads
- ✅ Can enter API key
- ✅ Can make queries
- ✅ Responses appear
- ✅ Metrics display

### Everything Working
- ✅ Backend + Frontend connected
- ✅ Cache persisting
- ✅ Database storing keys
- ✅ Semantic matching works
- ✅ Typo tolerance works

## 📝 Quick Commands Reference

```bash
# Start backend
cd backend && python semantic_cache_server.py

# Start frontend
cd frontend && npm run dev

# Test backend
cd backend && python test_api.py

# Check status
curl http://localhost:8000/health

# List API keys
cd backend && python api_key_generator.py --list

# Clear cache
rm backend/cache_data/cache.pkl
```

---

**That's it! Your system should be plug and play ready!** 🚀
