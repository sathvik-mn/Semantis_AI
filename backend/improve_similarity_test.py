"""
Test script to verify improved similarity matching
Tests queries like "what is computer" vs "what is the computer"
"""
import requests
import time

BASE_URL = "http://localhost:8000"
API_KEY = "Bearer sc-test-similarity"

def test_query(prompt, expected_hit_type=None):
    """Test a query and return the result."""
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        meta = result.get("meta", {})
        hit_type = meta.get("hit")
        similarity = meta.get("similarity", 0)
        latency = meta.get("latency_ms", 0)
        
        print(f"Query: '{prompt}'")
        print(f"  Hit: {hit_type}, Similarity: {similarity:.4f}, Latency: {latency}ms")
        if expected_hit_type and hit_type != expected_hit_type:
            print(f"  [WARN] Expected {expected_hit_type}, got {hit_type}")
        else:
            print(f"  [OK] Match")
        print()
        
        return hit_type, similarity
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None, 0

def main():
    """Test similarity matching improvements."""
    print("=" * 60)
    print("Testing Improved Similarity Matching")
    print("=" * 60)
    print()
    
    # Test 1: "what is computer" vs "what is the computer"
    print("Test 1: Basic similarity test")
    print("-" * 60)
    test_query("what is computer", "miss")  # First query - should be miss
    time.sleep(1)
    test_query("what is the computer", "semantic")  # Should be semantic hit
    
    # Test 2: Similar queries with articles
    print("\nTest 2: Articles test")
    print("-" * 60)
    test_query("explain machine learning", "miss")
    time.sleep(1)
    test_query("explain the machine learning", "semantic")
    
    # Test 3: Plural/singular
    print("\nTest 3: Plural/singular test")
    print("-" * 60)
    test_query("what are computers", "miss")
    time.sleep(1)
    test_query("what is computer", "semantic")
    
    # Get metrics
    print("\nFinal Metrics:")
    print("-" * 60)
    headers = {"Authorization": API_KEY}
    response = requests.get(f"{BASE_URL}/metrics", headers=headers)
    if response.status_code == 200:
        metrics = response.json()
        print(f"Total Requests: {metrics.get('total_requests', 0)}")
        print(f"Semantic Hits: {metrics.get('semantic_hits', 0)}")
        print(f"Hit Ratio: {metrics.get('hit_ratio', 0):.1%}")
        print(f"Semantic Hit Ratio: {metrics.get('semantic_hit_ratio', 0):.1%}")
        print(f"Similarity Threshold: {metrics.get('sim_threshold', 0)}")

if __name__ == "__main__":
    main()

