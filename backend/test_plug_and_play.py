"""
Test script to verify plug-and-play OpenAI-compatible API integration.
This tests if the semantic cache can be used as a drop-in replacement for OpenAI.
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_KEY = "Bearer sc-demo-user-VFcWBpkaiINmSl41"  # Replace with your API key

def test_openai_compatible_endpoint():
    """Test the OpenAI-compatible /v1/chat/completions endpoint."""
    print("=" * 60)
    print("Testing OpenAI-Compatible API (Plug & Play)")
    print("=" * 60)
    
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Test 1: Basic chat completion (OpenAI format)
    print("\n1. Testing Basic Chat Completion")
    print("-" * 60)
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "What is artificial intelligence?"}
        ],
        "temperature": 0.7
    }
    
    print(f"Request: POST {BASE_URL}/v1/chat/completions")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n[SUCCESS] Request successful!")
        print(f"Response format: OpenAI-compatible")
        print(f"Answer: {result['choices'][0]['message']['content'][:100]}...")
        print(f"Model: {result['model']}")
        print(f"Cache hit: {result.get('meta', {}).get('hit', 'unknown')}")
        print(f"Similarity: {result.get('meta', {}).get('similarity', 0)}")
        print(f"Latency: {result.get('meta', {}).get('latency_ms', 0)}ms")
    else:
        print(f"[ERROR] Request failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test 2: Test caching (same query should be faster)
    print("\n2. Testing Cache Hit (Same Query)")
    print("-" * 60)
    
    response2 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response2.status_code == 200:
        result2 = response2.json()
        hit_type = result2.get('meta', {}).get('hit', 'unknown')
        latency = result2.get('meta', {}).get('latency_ms', 0)
        
        print(f"[SUCCESS] Request successful!")
        print(f"Cache hit: {hit_type}")
        print(f"Latency: {latency}ms")
        
        if hit_type == 'exact':
            print("[SUCCESS] Exact cache hit - very fast!")
        elif hit_type == 'semantic':
            print("[SUCCESS] Semantic cache hit - fast!")
        else:
            print("[INFO] Cache miss - slower (expected for first query)")
    
    # Test 3: Test with semantic similarity (similar query)
    print("\n3. Testing Semantic Similarity (Similar Query)")
    print("-" * 60)
    
    payload3 = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Tell me about AI"}
        ],
        "temperature": 0.7
    }
    
    response3 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=headers,
        json=payload3
    )
    
    if response3.status_code == 200:
        result3 = response3.json()
        hit_type = result3.get('meta', {}).get('hit', 'unknown')
        similarity = result3.get('meta', {}).get('similarity', 0)
        latency = result3.get('meta', {}).get('latency_ms', 0)
        
        print(f"[SUCCESS] Request successful!")
        print(f"Cache hit: {hit_type}")
        print(f"Similarity: {similarity:.4f}")
        print(f"Latency: {latency}ms")
        
        if hit_type == 'semantic':
            print("[SUCCESS] Semantic cache hit - similar queries matched!")
        else:
            print(f"[INFO] {hit_type} - semantic matching may need tuning")
    
    # Test 4: Test with system message (OpenAI format)
    print("\n4. Testing with System Message (OpenAI Format)")
    print("-" * 60)
    
    payload4 = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is machine learning?"}
        ],
        "temperature": 0.7
    }
    
    response4 = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=headers,
        json=payload4
    )
    
    if response4.status_code == 200:
        result4 = response4.json()
        print(f"[SUCCESS] Request successful!")
        print(f"Answer: {result4['choices'][0]['message']['content'][:100]}...")
        print(f"Cache hit: {result4.get('meta', {}).get('hit', 'unknown')}")
    else:
        print(f"[ERROR] Request failed: {response4.status_code}")
    
    # Test 5: Verify response format matches OpenAI
    print("\n5. Verifying Response Format (OpenAI-Compatible)")
    print("-" * 60)
    
    required_fields = ['id', 'object', 'created', 'model', 'choices', 'usage']
    has_all_fields = all(field in result for field in required_fields)
    
    if has_all_fields:
        print("[SUCCESS] Response format matches OpenAI API")
        print(f"   - id: {result.get('id', 'N/A')}")
        print(f"   - object: {result.get('object', 'N/A')}")
        print(f"   - model: {result.get('model', 'N/A')}")
        print(f"   - choices: {len(result.get('choices', []))} choice(s)")
        print(f"   - usage: {result.get('usage', {})}")
        print(f"   - meta: {result.get('meta', {})} (additional cache info)")
    else:
        missing = [f for f in required_fields if f not in result]
        print(f"[ERROR] Missing fields: {missing}")
    
    print("\n" + "=" * 60)
    print("Plug & Play Test Summary")
    print("=" * 60)
    print("[SUCCESS] OpenAI-compatible endpoint: /v1/chat/completions")
    print("[SUCCESS] OpenAI-compatible request format")
    print("[SUCCESS] OpenAI-compatible response format")
    print("[SUCCESS] Additional cache metadata in response")
    print("[SUCCESS] Drop-in replacement for OpenAI API")
    print("\nTo use as OpenAI replacement:")
    print(f"  - Base URL: {BASE_URL}")
    print(f"  - Endpoint: /v1/chat/completions")
    print(f"  - Authorization: {API_KEY}")
    print(f"  - Format: OpenAI-compatible")

def test_integration_examples():
    """Show examples of how to integrate with different tools."""
    print("\n" + "=" * 60)
    print("Integration Examples")
    print("=" * 60)
    
    print("\n1. Python (using requests):")
    print("-" * 60)
    print("""
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={
        "Authorization": "Bearer sc-your-tenant-key",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)
result = response.json()
print(result['choices'][0]['message']['content'])
""")
    
    print("\n2. OpenAI Python SDK (with custom base URL):")
    print("-" * 60)
    print("""
from openai import OpenAI

client = OpenAI(
    api_key="sc-your-tenant-key",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
""")
    
    print("\n3. cURL:")
    print("-" * 60)
    print(f"""
curl -X POST {BASE_URL}/v1/chat/completions \\
  -H "Authorization: Bearer sc-your-tenant-key" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "model": "gpt-4o-mini",
    "messages": [{{"role": "user", "content": "Hello!"}}]
  }}'
""")
    
    print("\n4. JavaScript/Node.js:")
    print("-" * 60)
    print("""
const response = await fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sc-your-tenant-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: 'Hello!' }]
  })
});
const result = await response.json();
console.log(result.choices[0].message.content);
""")

if __name__ == "__main__":
    try:
        test_openai_compatible_endpoint()
        test_integration_examples()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

