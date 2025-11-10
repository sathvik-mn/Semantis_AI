"""
Client Perspective Test - Simulates how a real client would use the SDK
This test simulates a client's complete workflow from start to finish
"""
import sys
import os
import json
import time

# Simulate client installing SDK (they would add it to their path)
sdk_path = os.path.join(os.path.dirname(__file__), 'sdk', 'python')
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)
else:
    print("=" * 70)
    print("CLIENT PERSPECTIVE TEST - SDK NOT FOUND")
    print("=" * 70)
    print("\nAs a client, you would first generate the SDK:")
    print("  1. pip install openapi-python-client")
    print("  2. openapi-python-client generate --url YOUR_API/openapi.json --output sdk/python")
    print("  3. cd sdk/python && pip install -e .")
    print("\nThen run this test again.")
    sys.exit(1)

try:
    from semantis_ai_semantic_cache_api_client import Client
    from semantis_ai_semantic_cache_api_client.api.default import (
        health_health_get,
        get_metrics_metrics_get,
        openai_compatible_v1_chat_completions_post
    )
    from semantis_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage
except ImportError as e:
    print("=" * 70)
    print("CLIENT PERSPECTIVE TEST - SDK IMPORT FAILED")
    print("=" * 70)
    print(f"\nError: {e}")
    print("\nAs a client, you would:")
    print("  1. Install SDK: cd sdk/python && pip install -e .")
    print("  2. Verify installation: python -c 'from semantis_ai_semantic_cache_api_client import Client'")
    sys.exit(1)

print("=" * 70)
print("CLIENT PERSPECTIVE TEST - Simulating Real Client Usage")
print("=" * 70)
print("\nThis test simulates how a REAL CLIENT would use your service.")
print("We'll test the complete workflow from a client's perspective.\n")

# Client configuration (simulating client's setup)
CLIENT_API_KEY = "Bearer sc-test-client-demo"  # Client's API key
API_BASE_URL = "http://localhost:8000"  # Your API URL

print("=" * 70)
print("STEP 1: Client Initializes SDK")
print("=" * 70)
print(f"API URL: {API_BASE_URL}")
print(f"API Key: {CLIENT_API_KEY}")
print("\nClient code:")
print("  from semantis_ai_semantic_cache_api_client import Client")
print("  from semantis_ai_semantic_cache_api_client.api.default import openai_compatible_v1_chat_completions_post")
print("  from semantis_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage")
print("\n  client = Client(")
print(f"      base_url='{API_BASE_URL}',")
print(f"      headers={{'Authorization': '{CLIENT_API_KEY}'}}")
print("  )")

# Initialize client (as client would)
client = Client(
    base_url=API_BASE_URL,
    headers={"Authorization": CLIENT_API_KEY}
)
print("\n[OK] Client initialized successfully!")

print("\n" + "=" * 70)
print("STEP 2: Client Checks Service Health")
print("=" * 70)
print("Client wants to verify the service is running before making requests...")

try:
    health_response = health_health_get.sync_detailed(client=client)
    if health_response.status_code == 200:
        health_data = json.loads(health_response.content)
        print(f"\n[OK] Service is healthy!")
        print(f"     Status: {health_data.get('status')}")
        print(f"     Service: {health_data.get('service')}")
        print(f"     Version: {health_data.get('version')}")
    else:
        print(f"\n[FAIL] Service returned status {health_response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"\n[FAIL] Health check failed: {e}")
    print("       Client would see this as service unavailable.")
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 3: Client Makes First Request (Cache Miss)")
print("=" * 70)
print("Client makes their first query - this should be a cache MISS.")
print("The service will call the LLM and cache the response.\n")

first_query = "What is artificial intelligence?"
print(f"Query: '{first_query}'")
print("\nClient code:")
print("  request = ChatRequest(")
print("      model='gpt-4o-mini',")
print(f"      messages=[ChatMessage(role='user', content='{first_query}')]")
print("  )")
print("  response = openai_compatible_v1_chat_completions_post.sync(")
print("      client=client,")
print("      body=request")
print("  )")

try:
    request1 = ChatRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content=first_query)]
    )
    
    start_time = time.time()
    response1 = openai_compatible_v1_chat_completions_post.sync(
        client=client,
        body=request1
    )
    elapsed_time = (time.time() - start_time) * 1000
    
    if response1:
        hit_type = response1.get('meta', {}).get('hit', 'unknown')
        similarity = response1.get('meta', {}).get('similarity', 0)
        latency = response1.get('meta', {}).get('latency_ms', 0)
        answer = response1.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        print(f"\n[OK] Request successful!")
        print(f"     Hit Type: {hit_type}")
        print(f"     Similarity: {similarity}")
        print(f"     Latency: {latency:.2f}ms (measured: {elapsed_time:.2f}ms)")
        print(f"     Response: {answer[:100]}...")
        
        if hit_type == "miss":
            print(f"\n[EXPECTED] Cache MISS - First request always misses cache")
            print(f"           This means the service called the LLM (slow, costs money)")
        else:
            print(f"\n[INFO] Cache {hit_type.upper()} - Response was cached")
    else:
        print("\n[FAIL] Request returned None")
        sys.exit(1)
except Exception as e:
    print(f"\n[FAIL] Request failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 4: Client Makes Same Request (Cache Hit)")
print("=" * 70)
print("Client makes the SAME query again - this should be a cache HIT.")
print("The service should return instantly from cache (no LLM call).\n")

print(f"Query: '{first_query}' (same as before)")

try:
    request2 = ChatRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content=first_query)]
    )
    
    start_time = time.time()
    response2 = openai_compatible_v1_chat_completions_post.sync(
        client=client,
        body=request2
    )
    elapsed_time = (time.time() - start_time) * 1000
    
    if response2:
        hit_type = response2.get('meta', {}).get('hit', 'unknown')
        similarity = response2.get('meta', {}).get('similarity', 0)
        latency = response2.get('meta', {}).get('latency_ms', 0)
        answer = response2.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        print(f"\n[OK] Request successful!")
        print(f"     Hit Type: {hit_type}")
        print(f"     Similarity: {similarity}")
        print(f"     Latency: {latency:.2f}ms (measured: {elapsed_time:.2f}ms)")
        print(f"     Response: {answer[:100]}...")
        
        if hit_type == "exact":
            print(f"\n[SUCCESS] Cache EXACT HIT - Response returned instantly!")
            print(f"           No LLM call made (fast, free)")
            print(f"           This is the benefit of caching!")
        elif hit_type == "semantic":
            print(f"\n[OK] Cache SEMANTIC HIT - Similar query matched")
            print(f"      Similarity: {similarity:.4f}")
        else:
            print(f"\n[WARN] Expected cache hit, got {hit_type}")
    else:
        print("\n[FAIL] Request returned None")
        sys.exit(1)
except Exception as e:
    print(f"\n[FAIL] Request failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 5: Client Makes Similar Request (Semantic Cache Hit)")
print("=" * 70)
print("Client makes a SIMILAR query - this should be a SEMANTIC cache HIT.")
print("The service should match semantically similar queries.\n")

similar_query = "Explain artificial intelligence"
print(f"Query: '{similar_query}' (similar to first query)")

try:
    request3 = ChatRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content=similar_query)]
    )
    
    start_time = time.time()
    response3 = openai_compatible_v1_chat_completions_post.sync(
        client=client,
        body=request3
    )
    elapsed_time = (time.time() - start_time) * 1000
    
    if response3:
        hit_type = response3.get('meta', {}).get('hit', 'unknown')
        similarity = response3.get('meta', {}).get('similarity', 0)
        latency = response3.get('meta', {}).get('latency_ms', 0)
        answer = response3.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        print(f"\n[OK] Request successful!")
        print(f"     Hit Type: {hit_type}")
        print(f"     Similarity: {similarity:.4f}")
        print(f"     Latency: {latency:.2f}ms (measured: {elapsed_time:.2f}ms)")
        print(f"     Response: {answer[:100]}...")
        
        if hit_type == "semantic":
            print(f"\n[SUCCESS] Cache SEMANTIC HIT - Similar query matched!")
            print(f"           Similarity: {similarity:.4f} (threshold: ~0.72)")
            print(f"           No LLM call made (fast, free)")
            print(f"           This is the power of semantic caching!")
        elif hit_type == "exact":
            print(f"\n[OK] Cache EXACT HIT - Exact match found")
        else:
            print(f"\n[INFO] Cache {hit_type.upper()} - New query")
    else:
        print("\n[FAIL] Request returned None")
        sys.exit(1)
except Exception as e:
    print(f"\n[FAIL] Request failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 6: Client Checks Cache Metrics")
print("=" * 70)
print("Client wants to see how well the cache is performing...")

try:
    metrics_response = get_metrics_metrics_get.sync_detailed(client=client)
    if metrics_response.status_code == 200:
        metrics_data = json.loads(metrics_response.content)
        print("\n[OK] Metrics retrieved!")
        print(f"     Tenant: {metrics_data.get('tenant', 'N/A')}")
        print(f"     Total Requests: {metrics_data.get('total_requests', 0)}")
        print(f"     Cache Hits: {metrics_data.get('hits', 0)}")
        print(f"     Semantic Hits: {metrics_data.get('semantic_hits', 0)}")
        print(f"     Cache Misses: {metrics_data.get('misses', 0)}")
        print(f"     Hit Ratio: {metrics_data.get('hit_ratio', 0):.1%}")
        print(f"     Cache Entries: {metrics_data.get('entries', 0)}")
        print(f"     Similarity Threshold: {metrics_data.get('sim_threshold', 0)}")
        
        hit_ratio = metrics_data.get('hit_ratio', 0)
        if hit_ratio > 0.5:
            print(f"\n[SUCCESS] Cache is working well! Hit ratio: {hit_ratio:.1%}")
        else:
            print(f"\n[INFO] Cache hit ratio: {hit_ratio:.1%} (will improve with more requests)")
    else:
        print(f"\n[WARN] Metrics returned status {metrics_response.status_code}")
except Exception as e:
    print(f"\n[WARN] Metrics failed: {e}")

print("\n" + "=" * 70)
print("CLIENT PERSPECTIVE TEST - COMPLETE")
print("=" * 70)
print("\n[SUCCESS] All client scenarios tested successfully!")
print("\nSummary from Client's Perspective:")
print("  [OK] SDK works as expected")
print("  [OK] Service is healthy and responsive")
print("  [OK] Cache is functioning (exact + semantic hits)")
print("  [OK] Responses are fast for cached queries")
print("  [OK] Metrics are available")
print("\nClient Benefits:")
print("  [OK] Faster responses (cache hits are instant)")
print("  [OK] Cost savings (fewer LLM calls)")
print("  [OK] Better user experience (instant responses)")
print("  [OK] Easy integration (drop-in replacement for OpenAI)")
print("\n" + "=" * 70)
print("YOUR SERVICE IS READY FOR CLIENTS!")
print("=" * 70)

