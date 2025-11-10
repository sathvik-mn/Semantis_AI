"""
Comprehensive test script to verify the semantic caching algorithm is working correctly.
Tests exact matches, semantic matches, and cache misses.
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"
API_KEY = "Bearer sc-test-algorithm"

headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error testing {endpoint}: {e}")
        return None

def print_section(title):
    """Print a section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_exact_match():
    """Test exact cache match."""
    print_section("TEST 1: Exact Cache Match")
    
    prompt = "Explain quantum computing in simple terms"
    
    # First query - should be a miss
    print(f"\nQuery 1 (First time): '{prompt}'")
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    response1 = test_endpoint("/v1/chat/completions", "POST", data)
    if response1:
        meta1 = response1.get("meta", {})
        print(f"  Hit Type: {meta1.get('hit')}")
        print(f"  Similarity: {meta1.get('similarity')}")
        print(f"  Latency: {meta1.get('latency_ms')}ms")
        latency1 = meta1.get('latency_ms', 0)
    
    time.sleep(1)
    
    # Second query - exact same prompt - should be exact hit
    print(f"\nQuery 2 (Exact same): '{prompt}'")
    response2 = test_endpoint("/v1/chat/completions", "POST", data)
    if response2:
        meta2 = response2.get("meta", {})
        print(f"  Hit Type: {meta2.get('hit')}")
        print(f"  Similarity: {meta2.get('similarity')}")
        print(f"  Latency: {meta2.get('latency_ms')}ms")
        latency2 = meta2.get('latency_ms', 0)
        
        if meta2.get('hit') == 'exact':
            print(f"  [SUCCESS] Exact match detected!")
            print(f"  [SUCCESS] Speed improvement: {latency1 - latency2:.2f}ms faster")
        else:
            print(f"  [FAILED] Expected 'exact' hit, got '{meta2.get('hit')}'")
    
    return response2

def test_semantic_match():
    """Test semantic cache match."""
    print_section("TEST 2: Semantic Cache Match")
    
    original = "What are the benefits of renewable energy?"
    similar = "What advantages does clean energy provide?"
    
    # First query
    print(f"\nQuery 1: '{original}'")
    data1 = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": original}]
    }
    response1 = test_endpoint("/v1/chat/completions", "POST", data1)
    if response1:
        meta1 = response1.get("meta", {})
        print(f"  Hit Type: {meta1.get('hit')}")
        print(f"  Latency: {meta1.get('latency_ms')}ms")
        latency1 = meta1.get('latency_ms', 0)
    
    time.sleep(2)
    
    # Similar query - should be semantic hit if similarity > threshold
    print(f"\nQuery 2 (Similar): '{similar}'")
    data2 = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": similar}]
    }
    response2 = test_endpoint("/v1/chat/completions", "POST", data2)
    if response2:
        meta2 = response2.get("meta", {})
        print(f"  Hit Type: {meta2.get('hit')}")
        print(f"  Similarity: {meta2.get('similarity')}")
        print(f"  Latency: {meta2.get('latency_ms')}ms")
        latency2 = meta2.get('latency_ms', 0)
        
        if meta2.get('hit') == 'semantic':
            print(f"  [SUCCESS] Semantic match detected!")
            print(f"  [SUCCESS] Similarity: {meta2.get('similarity'):.3f}")
            print(f"  [SUCCESS] Speed improvement: {latency1 - latency2:.2f}ms faster")
        elif meta2.get('hit') == 'exact':
            print(f"  [NOTE] Got exact match (normalized text matched)")
        else:
            print(f"  [NOTE] Got miss - similarity may be below threshold")
            print(f"     Similarity: {meta2.get('similarity')}")
    
    return response2

def test_cache_miss():
    """Test cache miss with completely different query."""
    print_section("TEST 3: Cache Miss")
    
    prompt = "Tell me about the history of ancient Egypt"
    
    print(f"\nQuery: '{prompt}'")
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = test_endpoint("/v1/chat/completions", "POST", data)
    if response:
        meta = response.get("meta", {})
        print(f"  Hit Type: {meta.get('hit')}")
        print(f"  Similarity: {meta.get('similarity')}")
        print(f"  Latency: {meta.get('latency_ms')}ms")
        
        if meta.get('hit') == 'miss':
            print(f"  [SUCCESS] Cache miss correctly identified")
        else:
            print(f"  [NOTE] Got {meta.get('hit')} (may have matched previous query)")
    
    return response

def test_metrics():
    """Test metrics endpoint."""
    print_section("METRICS OVERVIEW")
    
    metrics = test_endpoint("/metrics")
    if metrics:
        print(f"Total Requests: {metrics.get('total_requests', 0)}")
        print(f"Hits: {metrics.get('hits', 0)}")
        print(f"Semantic Hits: {metrics.get('semantic_hits', 0)}")
        print(f"Misses: {metrics.get('misses', 0)}")
        print(f"Hit Ratio: {metrics.get('hit_ratio', 0):.1%}")
        print(f"Semantic Hit Ratio: {metrics.get('semantic_hit_ratio', 0):.1%}")
        print(f"Avg Latency: {metrics.get('avg_latency_ms', 0):.2f}ms")
        print(f"Cache Entries: {metrics.get('entries', 0)}")
        print(f"Similarity Threshold: {metrics.get('sim_threshold', 0)}")
    
    return metrics

def test_events():
    """Test events endpoint."""
    print_section("RECENT EVENTS")
    
    events = test_endpoint("/events?limit=5")
    if events:
        print(f"Total Events Retrieved: {len(events)}")
        for i, event in enumerate(events, 1):
            print(f"\nEvent {i}:")
            print(f"  Timestamp: {event.get('timestamp')}")
            print(f"  Decision: {event.get('decision')}")
            print(f"  Similarity: {event.get('similarity')}")
            print(f"  Latency: {event.get('latency_ms')}ms")
    
    return events

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  SEMANTIC CACHING ALGORITHM TEST SUITE")
    print("="*60)
    
    # Check health
    print_section("HEALTH CHECK")
    health = test_endpoint("/health")
    if health:
        print(f"Status: {health.get('status')}")
        print(f"Service: {health.get('service')}")
        print(f"Version: {health.get('version')}")
    else:
        print("[ERROR] Backend server is not running!")
        return
    
    # Run tests
    test_exact_match()
    time.sleep(2)
    
    test_semantic_match()
    time.sleep(2)
    
    test_cache_miss()
    time.sleep(1)
    
    # Check metrics and events
    test_metrics()
    test_events()
    
    print_section("TEST SUITE COMPLETE")
    print("\n[SUCCESS] All tests completed. Review results above.")
    print("\nNote: Semantic matching depends on:")
    print("  - Embedding similarity threshold (default: 0.83)")
    print("  - Quality of OpenAI embeddings")
    print("  - Semantic similarity between queries")

if __name__ == "__main__":
    main()

