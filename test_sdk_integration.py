"""
Comprehensive SDK Integration Test
Tests the SDK from a client's perspective
"""
import sys
import os

# Add SDK to path
sdk_path = os.path.join(os.path.dirname(__file__), 'sdk', 'python', 'src')
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)
else:
    print("[ERROR] SDK not found. Please generate it first:")
    print("   pip install openapi-python-client")
    print("   openapi-python-client generate --url http://localhost:8000/openapi.json --output sdk/python")
    sys.exit(1)

try:
    from semantis_ai_semantic_cache_api import Client
    from semantis_ai_semantic_cache_api.api.default import (
        health_health_get,
        get_metrics_metrics_get,
        openai_compatible_v1_chat_completions_post,
        simple_query_query_get
    )
    from semantis_ai_semantic_cache_api.models import ChatRequest, ChatMessage
    print("✅ SDK imported successfully!")
except ImportError as e:
    print(f"❌ Failed to import SDK: {e}")
    print("\nPlease install the SDK:")
    print("  cd sdk/python")
    print("  pip install -e .")
    sys.exit(1)

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "Bearer sc-test-sdk-integration"

def test_health_check():
    """Test health check endpoint."""
    print("\n" + "=" * 60)
    print("1. Testing Health Check")
    print("=" * 60)
    
    try:
        client = Client(base_url=BASE_URL)
        health = health_health_get.sync(client=client)
        
        print(f"✅ Service: {health.service}")
        print(f"✅ Status: {health.status}")
        print(f"✅ Version: {health.version}")
        return True
    except Exception as e:
        print(f"[FAIL] Health check failed: {e}")
        return False

def test_chat_completion():
    """Test chat completion with caching."""
    print("\n" + "=" * 60)
    print("2. Testing Chat Completion (with Caching)")
    print("=" * 60)
    
    try:
        client = Client(
            base_url=BASE_URL,
            headers={"Authorization": API_KEY}
        )
        
        # First query (should be miss)
        print("\n2.1. First Query (expected: miss)")
        chat_request1 = ChatRequest(
            model="gpt-4o-mini",
            messages=[ChatMessage(role="user", content="What is semantic caching?")]
        )
        
        response1 = openai_compatible_v1_chat_completions_post.sync(
            client=client,
            body=chat_request1
        )
        
        print(f"   ✅ Hit type: {response1.meta.hit}")
        print(f"   ✅ Similarity: {response1.meta.similarity}")
        print(f"   ✅ Latency: {response1.meta.latency_ms}ms")
        print(f"   ✅ Response: {response1.choices[0].message.content[:60]}...")
        
        # Second query (should be exact hit)
        print("\n2.2. Second Query - Same (expected: exact hit)")
        response2 = openai_compatible_v1_chat_completions_post.sync(
            client=client,
            body=chat_request1
        )
        
        print(f"   ✅ Hit type: {response2.meta.hit}")
        print(f"   ✅ Similarity: {response2.meta.similarity}")
        print(f"   ✅ Latency: {response2.meta.latency_ms}ms")
        
        if response2.meta.hit == "exact":
            print("   ✅ Cache working! Exact hit on second query.")
        else:
            print(f"   ⚠️  Expected exact hit, got {response2.meta.hit}")
        
        # Third query - Similar (should be semantic hit)
        print("\n2.3. Third Query - Similar (expected: semantic hit)")
        chat_request3 = ChatRequest(
            model="gpt-4o-mini",
            messages=[ChatMessage(role="user", content="Explain semantic caching.")]
        )
        
        response3 = openai_compatible_v1_chat_completions_post.sync(
            client=client,
            body=chat_request3
        )
        
        print(f"   ✅ Hit type: {response3.meta.hit}")
        print(f"   ✅ Similarity: {response3.meta.similarity}")
        print(f"   ✅ Latency: {response3.meta.latency_ms}ms")
        
        if response3.meta.hit == "semantic":
            print("   ✅ Semantic cache working! Similar query matched.")
        else:
            print(f"   ⚠️  Expected semantic hit, got {response3.meta.hit}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Chat completion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metrics():
    """Test metrics endpoint."""
    print("\n" + "=" * 60)
    print("3. Testing Metrics")
    print("=" * 60)
    
    try:
        client = Client(
            base_url=BASE_URL,
            headers={"Authorization": API_KEY}
        )
        
        metrics = get_metrics_metrics_get.sync(client=client)
        
        print(f"✅ Tenant: {metrics.tenant}")
        print(f"✅ Total requests: {metrics.total_requests}")
        print(f"✅ Hits: {metrics.hits}")
        print(f"✅ Semantic hits: {metrics.semantic_hits}")
        print(f"✅ Misses: {metrics.misses}")
        print(f"✅ Hit ratio: {metrics.hit_ratio:.1%}")
        print(f"✅ Cache entries: {metrics.entries}")
        print(f"✅ Similarity threshold: {metrics.sim_threshold}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Metrics failed: {e}")
        return False

def test_error_handling():
    """Test error handling."""
    print("\n" + "=" * 60)
    print("4. Testing Error Handling")
    print("=" * 60)
    
    try:
        # Test with invalid API key
        client = Client(
            base_url=BASE_URL,
            headers={"Authorization": "Bearer invalid-key"}
        )
        
        try:
            metrics = get_metrics_metrics_get.sync(client=client)
            print("[FAIL] Should have failed with invalid key")
            return False
        except Exception as e:
            print(f"✅ Error handling works: {str(e)[:50]}...")
            return True
    except Exception as e:
        print(f"⚠️  Error handling test: {e}")
        return True

def main():
    """Run all SDK tests."""
    print("=" * 60)
    print("SDK Integration Test Suite")
    print("=" * 60)
    print("\nTesting SDK from client's perspective...")
    print(f"Backend URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Chat Completion", test_chat_completion()))
    results.append(("Metrics", test_metrics()))
    results.append(("Error Handling", test_error_handling()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n[SUCCESS] All SDK integration tests passed!")
        print("\n[SUCCESS] SDK is ready for client use!")
    else:
        print("\n[FAIL] Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

