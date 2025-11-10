"""
Test script specifically for typo matching: "what is comptr" vs "what iz comptr"
"""
import requests
import time

BASE_URL = "http://localhost:8000"
API_KEY = "Bearer sc-typo-test-fresh"

def clear_cache_and_test():
    """Test with fresh cache to ensure we're testing semantic matching."""
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }
    
    print("=" * 60)
    print("Testing Typo Matching: 'what is comptr' vs 'what iz comptr'")
    print("=" * 60)
    print("\nUsing fresh tenant to ensure clean cache...")
    
    # Query 1: "what is comptr" (first time - should be miss)
    print("\n1. Query: 'what is comptr' (first time)")
    print("   Expected: MISS (first query, nothing in cache)")
    
    data1 = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "what is comptr"}]
    }
    
    response1 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=headers,
        json=data1
    )
    
    if response1.status_code == 200:
        result1 = response1.json()
        meta1 = result1.get("meta", {})
        print(f"   Result: {meta1.get('hit')}")
        print(f"   Similarity: {meta1.get('similarity', 0):.4f}")
        print(f"   Latency: {meta1.get('latency_ms', 0):.2f}ms")
        
        if meta1.get('hit') != 'miss':
            print(f"   [WARNING] Expected miss but got {meta1.get('hit')}")
    else:
        print(f"   Error: {response1.status_code}")
        return
    
    time.sleep(2)
    
    # Query 2: "what iz comptr" (should match "what is comptr" semantically)
    print("\n2. Query: 'what iz comptr' (should match 'what is comptr')")
    print("   Expected: SEMANTIC HIT (similar to 'what is comptr')")
    
    data2 = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "what iz comptr"}]
    }
    
    response2 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=headers,
        json=data2
    )
    
    if response2.status_code == 200:
        result2 = response2.json()
        meta2 = result2.get("meta", {})
        hit2 = meta2.get('hit')
        sim2 = meta2.get('similarity', 0)
        threshold2 = meta2.get('threshold_used', 0.72)
        
        print(f"   Result: {hit2}")
        print(f"   Similarity: {sim2:.4f}")
        print(f"   Threshold: {threshold2}")
        print(f"   Latency: {meta2.get('latency_ms', 0):.2f}ms")
        
        if hit2 == 'semantic':
            print(f"\n   [SUCCESS] Semantic match found!")
            print(f"   Similarity {sim2:.4f} >= Threshold {threshold2}")
        elif hit2 == 'exact':
            print(f"\n   [INFO] Got exact match (normalized to same string)")
        else:
            print(f"\n   [ISSUE] Expected semantic match but got {hit2}")
            print(f"   Similarity {sim2:.4f} < Threshold {threshold2}")
            if sim2 > 0:
                print(f"   [NOTE] Similarity is {sim2:.4f}, which is below threshold {threshold2}")
                print(f"   [SUGGESTION] Threshold might be too high for typo tolerance")
    else:
        print(f"   Error: {response2.status_code}")
        return
    
    # Get metrics
    print("\n" + "=" * 60)
    print("Final Metrics:")
    response_metrics = requests.get(f"{BASE_URL}/metrics", headers=headers)
    if response_metrics.status_code == 200:
        metrics = response_metrics.json()
        print(f"Total Requests: {metrics.get('total_requests', 0)}")
        print(f"Hits: {metrics.get('hits', 0)}")
        print(f"Semantic Hits: {metrics.get('semantic_hits', 0)}")
        print(f"Misses: {metrics.get('misses', 0)}")
        print(f"Hit Ratio: {metrics.get('hit_ratio', 0):.1%}")
        print(f"Semantic Hit Ratio: {metrics.get('semantic_hit_ratio', 0):.1%}")
        print(f"Similarity Threshold: {metrics.get('sim_threshold', 0)}")
        print(f"Cache Entries: {metrics.get('entries', 0)}")

if __name__ == "__main__":
    clear_cache_and_test()

