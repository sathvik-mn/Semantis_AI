"""
Quick plug and play test script to verify everything is working
"""
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
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            health = r.json()
            print(f"   [OK] Backend is running")
            print(f"   Service: {health.get('service')}")
            print(f"   Version: {health.get('version')}")
        else:
            print(f"   [FAIL] Backend returned {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   [FAIL] Backend is not running")
        print("   [INFO] Start it with: cd backend && python semantic_cache_server.py")
        return False
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        return False
    
    # 2. Test query
    print("\n2. Test Query...")
    try:
        r = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={"Authorization": API_KEY, "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Hello, what is AI?"}]
            },
            timeout=30
        )
        if r.status_code == 200:
            result = r.json()
            hit_type = result.get('meta', {}).get('hit', 'unknown')
            similarity = result.get('meta', {}).get('similarity', 0)
            print(f"   [OK] Query successful")
            print(f"   Hit type: {hit_type}")
            print(f"   Similarity: {similarity:.4f}" if similarity > 0 else "   Similarity: N/A")
            response_text = result['choices'][0]['message']['content']
            print(f"   Response: {response_text[:60]}...")
        else:
            print(f"   [FAIL] Query failed: {r.status_code}")
            print(f"   Response: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"   [FAIL] Query error: {e}")
        return False
    
    # 3. Test metrics
    print("\n3. Metrics Check...")
    try:
        r = requests.get(
            f"{BASE_URL}/metrics",
            headers={"Authorization": API_KEY},
            timeout=5
        )
        if r.status_code == 200:
            metrics = r.json()
            print(f"   [OK] Metrics retrieved")
            print(f"   Cache entries: {metrics.get('entries', 0)}")
            print(f"   Total requests: {metrics.get('total_requests', 0)}")
            print(f"   Hit ratio: {metrics.get('hit_ratio', 0):.1%}")
            print(f"   Semantic hits: {metrics.get('semantic_hits', 0)}")
        else:
            print(f"   [WARN] Metrics failed: {r.status_code}")
    except Exception as e:
        print(f"   [WARN] Metrics error: {e}")
    
    # 4. Test cache persistence
    print("\n4. Cache Persistence Check...")
    import os
    cache_file = "cache_data/cache.pkl"
    if os.path.exists(cache_file):
        size = os.path.getsize(cache_file)
        print(f"   [OK] Cache file exists: {cache_file}")
        print(f"   Size: {size / 1024:.2f} KB")
    else:
        print(f"   [INFO] Cache file not found (will be created after queries)")
    
    # 5. Test database
    print("\n5. Database Check...")
    try:
        from database import list_api_keys
        keys = list_api_keys()
        print(f"   [OK] Database accessible")
        print(f"   API keys in database: {len(keys)}")
        if keys:
            print(f"   Sample keys:")
            for key in keys[:3]:
                print(f"     - {key.get('tenant_id')}: {key.get('plan')} plan")
    except Exception as e:
        print(f"   [WARN] Database check failed: {e}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All core tests passed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test frontend: http://localhost:3001")
    print("2. Test typo matching: python test_fresh_typo.py")
    print("3. Generate API keys: python api_key_generator.py --list")
    return True

if __name__ == "__main__":
    success = test()
    sys.exit(0 if success else 1)

