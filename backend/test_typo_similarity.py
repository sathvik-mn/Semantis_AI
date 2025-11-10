"""
Test script to check similarity scores for typo queries
"""
import requests
import time

BASE_URL = "http://localhost:8000"
API_KEY = "Bearer sc-test-typo-debug"

def test_queries():
    """Test queries with typos and check similarity scores."""
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }
    
    queries = [
        "what is comptr",
        "what iz comptr",
        "what is computer",
        "what is the computer",
        "what are computers",
    ]
    
    print("Testing queries with typos and checking similarity...")
    print("=" * 60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: '{query}'")
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": query}]
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
            threshold_used = meta.get("threshold_used", 0.78)
            
            print(f"   Hit: {hit_type}")
            print(f"   Similarity: {similarity:.4f}")
            print(f"   Threshold: {threshold_used}")
            print(f"   Latency: {latency}ms")
            
            if hit_type == "miss" and similarity > 0:
                print(f"   [NOTE] Missed with similarity {similarity:.4f} (threshold: {threshold_used})")
        else:
            print(f"   Error: {response.status_code}")
        
        time.sleep(1)
    
    # Get metrics
    print("\n" + "=" * 60)
    print("Final Metrics:")
    response = requests.get(f"{BASE_URL}/metrics", headers=headers)
    if response.status_code == 200:
        metrics = response.json()
        print(f"Total Requests: {metrics.get('total_requests', 0)}")
        print(f"Semantic Hits: {metrics.get('semantic_hits', 0)}")
        print(f"Hit Ratio: {metrics.get('hit_ratio', 0):.1%}")
        print(f"Similarity Threshold: {metrics.get('sim_threshold', 0)}")

if __name__ == "__main__":
    test_queries()

