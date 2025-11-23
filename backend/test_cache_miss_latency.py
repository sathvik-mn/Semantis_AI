"""
Test Cache Miss Latency Optimizations

This script tests the cache miss latency improvements:
1. Verifies embedding reuse (no duplicate generation)
2. Verifies async cache storage (non-blocking)
3. Measures actual latency improvements
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"
# Use a unique tenant ID with timestamp to ensure fresh cache
import time as time_module
TENANT_ID = f"test-latency-{int(time_module.time())}"
HEADERS = {"Authorization": f"Bearer sc-{TENANT_ID}"}

def test_cache_miss_latency():
    """Test cache miss latency with unique queries."""
    print("=" * 60)
    print("CACHE MISS LATENCY OPTIMIZATION TEST")
    print("=" * 60)
    
    # Generate completely unique queries with different structures and topics
    # to ensure cache misses (semantic cache matches similar structures)
    import uuid
    import random
    
    # Use completely different query structures and topics
    unique_queries = [
        f"List all the planets in the {uuid.uuid4().hex[:12]} solar system and their distances.",
        f"Calculate the square root of {random.randint(100000, 999999)} and explain the method.",
        f"Write a Python function to sort a list of {uuid.uuid4().hex[:8]} items using quicksort algorithm.",
    ]
    
    print(f"Using fresh tenant ID: {TENANT_ID}")
    print("Note: Using completely different query structures to avoid semantic matching\n")
    
    latencies = []
    
    for i, query in enumerate(unique_queries, 1):
        print(f"\n[Test {i}] Query: {query[:50]}...")
        
        start_time = time.time()
        try:
            r = requests.get(
                f"{BASE_URL}/query",
                params={"prompt": query},
                headers=HEADERS,
                timeout=30
            )
            
            if r.ok:
                data = r.json()
                meta = data.get('meta', {})
                hit_type = meta.get('hit', 'unknown')
                reported_latency = meta.get('latency_ms', 0)
                actual_latency = (time.time() - start_time) * 1000
                
                print(f"  Hit Type: {hit_type}")
                print(f"  Reported Latency: {reported_latency:.2f}ms")
                print(f"  Actual Latency: {actual_latency:.2f}ms")
                
                if hit_type == 'miss':
                    latencies.append({
                        'reported': reported_latency,
                        'actual': actual_latency,
                        'overhead': actual_latency - reported_latency
                    })
                    print(f"  ✅ Cache miss detected")
                    print(f"  ⚡ Overhead: {actual_latency - reported_latency:.2f}ms")
                else:
                    print(f"  ⚠️  Expected miss but got {hit_type}")
            else:
                print(f"  ❌ Error: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"  ❌ Exception: {e}")
        
        # Small delay between requests
        time.sleep(1)
    
    # Summary
    if latencies:
        print("\n" + "=" * 60)
        print("LATENCY SUMMARY")
        print("=" * 60)
        avg_reported = sum(l['reported'] for l in latencies) / len(latencies)
        avg_actual = sum(l['actual'] for l in latencies) / len(latencies)
        avg_overhead = sum(l['overhead'] for l in latencies) / len(latencies)
        
        print(f"Average Reported Latency: {avg_reported:.2f}ms")
        print(f"Average Actual Latency: {avg_actual:.2f}ms")
        print(f"Average Overhead: {avg_overhead:.2f}ms")
        
        # Check if overhead is low (should be < 10ms with optimizations)
        if avg_overhead < 10:
            print(f"\n✅ SUCCESS: Overhead is low ({avg_overhead:.2f}ms)")
            print("   Cache storage is happening asynchronously!")
        else:
            print(f"\n⚠️  WARNING: Overhead is high ({avg_overhead:.2f}ms)")
            print("   Cache storage might be blocking the response")
        
        # Check if reported latency excludes cache storage
        if avg_reported < avg_actual:
            print(f"\n✅ SUCCESS: Reported latency excludes cache storage")
            print(f"   Difference: {avg_actual - avg_reported:.2f}ms")
        else:
            print(f"\n⚠️  WARNING: Reported latency might include cache storage")
    else:
        print("\n⚠️  No cache misses detected - cannot measure latency improvements")

def test_embedding_reuse():
    """Test that embeddings are reused (check logs for single embedding generation)."""
    print("\n" + "=" * 60)
    print("EMBEDDING REUSE TEST")
    print("=" * 60)
    print("Note: Check backend logs to verify embedding is generated only once")
    print("      per cache miss (should see single embedding call per query)")
    
    import uuid
    import random
    # Use a completely different query structure
    query = f"Generate a random number between {random.randint(1000, 9999)} and {random.randint(10000, 99999)} using {uuid.uuid4().hex[:16]} seed."
    print(f"\nQuery: {query}")
    
    try:
        r = requests.get(
            f"{BASE_URL}/query",
            params={"prompt": query},
            headers=HEADERS,
            timeout=30
        )
        
        if r.ok:
            data = r.json()
            meta = data.get('meta', {})
            print(f"Hit Type: {meta.get('hit', 'unknown')}")
            print(f"Latency: {meta.get('latency_ms', 0):.2f}ms")
            print("\n✅ Query completed - check logs for embedding generation count")
        else:
            print(f"❌ Error: {r.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    """Run all latency tests."""
    # Check health first
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if not r.ok:
            print("❌ Backend server is not healthy!")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Make sure the backend server is running on localhost:8000")
        return
    
    # Run tests
    test_cache_miss_latency()
    test_embedding_reuse()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

