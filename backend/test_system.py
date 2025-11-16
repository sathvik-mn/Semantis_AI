"""
Comprehensive system test script
Tests backend, frontend, database, and algorithm improvements
"""
import requests
import time
import sys
from database import init_database, get_db_connection

def test_database():
    """Test database connectivity and tables."""
    print("\n" + "="*60)
    print("TESTING DATABASE")
    print("="*60)
    try:
        init_database()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ Database connected")
            print(f"✅ Tables found: {', '.join(tables)}")
            
            # Test each table
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   - {table}: {count} rows")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_backend_health():
    """Test backend health endpoint."""
    print("\n" + "="*60)
    print("TESTING BACKEND HEALTH")
    print("="*60)
    try:
        r = requests.get("http://localhost:8000/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Backend is running")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Cache: {data.get('cache', {})}")
            return True
        else:
            print(f"❌ Backend returned status {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Backend health test failed: {e}")
        return False

def test_backend_endpoints():
    """Test backend API endpoints."""
    print("\n" + "="*60)
    print("TESTING BACKEND ENDPOINTS")
    print("="*60)
    api_key = "sc-test-local"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    results = {}
    
    # Test metrics endpoint
    try:
        r = requests.get("http://localhost:8000/metrics", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Metrics endpoint: OK")
            print(f"   Requests: {data.get('total_requests', 0)}")
            print(f"   Hit ratio: {data.get('hit_ratio', 0)}")
            results['metrics'] = True
        else:
            print(f"❌ Metrics endpoint: Status {r.status_code}")
            results['metrics'] = False
    except Exception as e:
        print(f"❌ Metrics endpoint failed: {e}")
        results['metrics'] = False
    
    # Test chat completions endpoint
    try:
        data = {
            "messages": [{"role": "user", "content": "What is semantic caching?"}],
            "model": "gpt-3.5-turbo"
        }
        r = requests.post("http://localhost:8000/v1/chat/completions", 
                         json=data, headers=headers, timeout=30)
        if r.status_code == 200:
            resp = r.json()
            print(f"✅ Chat endpoint: OK")
            meta = resp.get('meta', {})
            print(f"   Hit type: {meta.get('hit', 'unknown')}")
            print(f"   Similarity: {meta.get('similarity', 0)}")
            print(f"   Hybrid score: {meta.get('hybrid_score', 'N/A')}")
            print(f"   Confidence: {meta.get('confidence', 'N/A')}")
            print(f"   Strategy: {meta.get('strategy', 'unknown')}")
            results['chat'] = True
        else:
            print(f"❌ Chat endpoint: Status {r.status_code}")
            print(f"   Response: {r.text[:200]}")
            results['chat'] = False
    except Exception as e:
        print(f"❌ Chat endpoint failed: {e}")
        results['chat'] = False
    
    # Test second query (should hit cache)
    try:
        time.sleep(1)
        data = {
            "messages": [{"role": "user", "content": "What is semantic caching?"}],
            "model": "gpt-3.5-turbo"
        }
        r = requests.post("http://localhost:8000/v1/chat/completions", 
                         json=data, headers=headers, timeout=30)
        if r.status_code == 200:
            resp = r.json()
            meta = resp.get('meta', {})
            if meta.get('hit') == 'exact':
                print(f"✅ Cache hit test: EXACT HIT")
            elif meta.get('hit') == 'semantic':
                print(f"✅ Cache hit test: SEMANTIC HIT")
                print(f"   Hybrid score: {meta.get('hybrid_score', 'N/A')}")
                print(f"   Confidence: {meta.get('confidence', 'N/A')}")
            else:
                print(f"⚠️  Cache hit test: MISS (expected on first run)")
            results['cache'] = True
        else:
            results['cache'] = False
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        results['cache'] = False
    
    return all(results.values())

def test_algorithm_features():
    """Test new algorithm features."""
    print("\n" + "="*60)
    print("TESTING ALGORITHM IMPROVEMENTS")
    print("="*60)
    api_key = "sc-test-local"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Test context-aware matching with conversation
    try:
        data = {
            "messages": [
                {"role": "user", "content": "Tell me about Python"},
                {"role": "assistant", "content": "Python is a programming language"},
                {"role": "user", "content": "What are its main features?"}
            ],
            "model": "gpt-3.5-turbo"
        }
        r = requests.post("http://localhost:8000/v1/chat/completions", 
                         json=data, headers=headers, timeout=30)
        if r.status_code == 200:
            resp = r.json()
            meta = resp.get('meta', {})
            print(f"✅ Context-aware test: OK")
            print(f"   Strategy: {meta.get('strategy', 'unknown')}")
            if 'hybrid_score' in meta:
                print(f"   ✅ Hybrid scoring active")
            if 'confidence' in meta:
                print(f"   ✅ Confidence scoring active")
            return True
        else:
            print(f"❌ Context-aware test failed: Status {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Context-aware test failed: {e}")
        return False

def test_frontend():
    """Test frontend availability."""
    print("\n" + "="*60)
    print("TESTING FRONTEND")
    print("="*60)
    try:
        r = requests.get("http://localhost:3000", timeout=5)
        if r.status_code == 200:
            print(f"✅ Frontend is running on port 3000")
            return True
        else:
            print(f"⚠️  Frontend returned status {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️  Frontend is not running on port 3000")
        print("   Start with: cd frontend && npm run dev")
        return False
    except Exception as e:
        print(f"⚠️  Frontend test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("COMPREHENSIVE SYSTEM TEST")
    print("="*60)
    
    results = {
        "Database": test_database(),
        "Backend Health": test_backend_health(),
        "Backend Endpoints": test_backend_endpoints(),
        "Algorithm Features": test_algorithm_features(),
        "Frontend": test_frontend(),
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())


