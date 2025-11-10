"""
Cache Warmup Script for Semantis AI
Pre-populates the cache with common queries to avoid LLM calls on first requests.
"""
import requests
import json
import time
from typing import List, Dict

BASE_URL = "http://localhost:8000"
API_KEY = "sc-test-local"  # Change this to your API key

def warmup_cache(queries: List[Dict[str, str]], api_key: str = API_KEY):
    """
    Pre-populate cache with common queries.
    
    Args:
        queries: List of query dictionaries with 'prompt' and optionally 'model'
        api_key: API key in format sc-{tenant}-{anything}
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"Warming up cache with {len(queries)} queries...")
    print(f"API Key: {api_key}")
    print(f"Base URL: {BASE_URL}")
    print("-" * 60)
    
    results = {
        "total": len(queries),
        "successful": 0,
        "failed": 0,
        "details": []
    }
    
    for i, query in enumerate(queries, 1):
        prompt = query.get("prompt", "")
        model = query.get("model", "gpt-4o-mini")
        
        print(f"\n[{i}/{len(queries)}] Processing: {prompt[:60]}...")
        
        try:
            # Make the API call
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                hit_type = result.get("meta", {}).get("hit", "miss")
                latency = result.get("meta", {}).get("latency_ms", 0)
                
                results["successful"] += 1
                results["details"].append({
                    "prompt": prompt,
                    "status": "success",
                    "hit_type": hit_type,
                    "latency_ms": latency
                })
                
                print(f"  [OK] Success - Hit: {hit_type}, Latency: {latency}ms")
            else:
                results["failed"] += 1
                results["details"].append({
                    "prompt": prompt,
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                })
                print(f"  [FAIL] Failed - HTTP {response.status_code}")
                
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "prompt": prompt,
                "status": "error",
                "error": str(e)
            })
            print(f"  [ERROR] Error: {str(e)}")
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("WARMUP SUMMARY")
    print("=" * 60)
    print(f"Total queries: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {(results['successful']/results['total']*100):.1f}%")
    
    return results

# Common queries for different domains
COMMON_QUERIES = [
    # General AI/ML questions
    {"prompt": "What is artificial intelligence?", "model": "gpt-4o-mini"},
    {"prompt": "Explain machine learning in simple terms", "model": "gpt-4o-mini"},
    {"prompt": "What is the difference between AI and ML?", "model": "gpt-4o-mini"},
    {"prompt": "How does deep learning work?", "model": "gpt-4o-mini"},
    {"prompt": "What is neural network?", "model": "gpt-4o-mini"},
    
    # Programming questions
    {"prompt": "What is Python programming language?", "model": "gpt-4o-mini"},
    {"prompt": "Explain REST API", "model": "gpt-4o-mini"},
    {"prompt": "What is Docker?", "model": "gpt-4o-mini"},
    {"prompt": "How does caching work?", "model": "gpt-4o-mini"},
    {"prompt": "What is semantic caching?", "model": "gpt-4o-mini"},
    
    # Business/General knowledge
    {"prompt": "What is the capital of France?", "model": "gpt-4o-mini"},
    {"prompt": "Explain quantum computing", "model": "gpt-4o-mini"},
    {"prompt": "What are the benefits of cloud computing?", "model": "gpt-4o-mini"},
    {"prompt": "How does blockchain work?", "model": "gpt-4o-mini"},
    {"prompt": "What is cybersecurity?", "model": "gpt-4o-mini"},
]

def load_queries_from_file(filepath: str) -> List[Dict[str, str]]:
    """Load queries from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "queries" in data:
                return data["queries"]
            else:
                print(f"Invalid file format. Expected list or dict with 'queries' key.")
                return []
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return []

def main():
    """Main function to run cache warmup."""
    import argparse
    global BASE_URL, API_KEY
    
    parser = argparse.ArgumentParser(description="Warm up the semantic cache with common queries")
    parser.add_argument("--api-key", type=str, default=API_KEY, help="API key (format: sc-{tenant}-{anything})")
    parser.add_argument("--url", type=str, default=BASE_URL, help="Backend API URL")
    parser.add_argument("--file", type=str, help="JSON file with queries to load")
    parser.add_argument("--queries", type=int, default=10, help="Number of common queries to use (if not using file)")
    
    args = parser.parse_args()
    
    BASE_URL = args.url
    API_KEY = args.api_key
    
    # Load queries
    if args.file:
        queries = load_queries_from_file(args.file)
        if not queries:
            print("No queries loaded from file. Using default queries.")
            queries = COMMON_QUERIES[:args.queries]
    else:
        queries = COMMON_QUERIES[:args.queries]
    
    if not queries:
        print("No queries to process.")
        return
    
    # Run warmup
    results = warmup_cache(queries, args.api_key)
    
    # Save results
    with open("warmup_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: warmup_results.json")

if __name__ == "__main__":
    main()

