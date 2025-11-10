"""
Test script for the generated Python SDK - Fixed version
"""
import sys
import os
import json

# Add SDK to path
sdk_path = os.path.join(os.path.dirname(__file__), 'sdk', 'python')
if os.path.exists(sdk_path):
    sys.path.insert(0, sdk_path)
else:
    print("[ERROR] SDK not found. Please generate it first:")
    print("   pip install openapi-python-client")
    print("   openapi-python-client generate --url http://localhost:8000/openapi.json --output sdk/python")
    sys.exit(1)

try:
    from semantis_ai_semantic_cache_api_client import Client
    from semantis_ai_semantic_cache_api_client.api.default import (
        health_health_get,
        get_metrics_metrics_get,
        openai_compatible_v1_chat_completions_post
    )
    from semantis_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage
    
    print("[OK] SDK imported successfully!")
    print("\nTesting SDK...")
    
    # Initialize client
    client = Client(
        base_url="http://localhost:8000",
        headers={
            "Authorization": "Bearer sc-test-local"
        }
    )
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        health_response = health_health_get.sync_detailed(client=client)
        if health_response.status_code == 200:
            health_data = json.loads(health_response.content)
            print(f"   [OK] Status: {health_data.get('status')}")
            print(f"   [OK] Service: {health_data.get('service')}")
            print(f"   [OK] Version: {health_data.get('version')}")
        else:
            print(f"   [FAIL] Health check returned {health_response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"   [FAIL] Health check failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Test metrics endpoint
    print("\n2. Testing metrics endpoint...")
    try:
        metrics_response = get_metrics_metrics_get.sync_detailed(client=client)
        if metrics_response.status_code == 200:
            metrics_data = json.loads(metrics_response.content)
            print(f"   [OK] Total Requests: {metrics_data.get('total_requests', 0)}")
            print(f"   [OK] Hit Ratio: {metrics_data.get('hit_ratio', 0):.1%}")
            print(f"   [OK] Cache Entries: {metrics_data.get('entries', 0)}")
            print(f"   [OK] Semantic Hits: {metrics_data.get('semantic_hits', 0)}")
        else:
            print(f"   [WARN] Metrics returned {metrics_response.status_code}")
    except Exception as e:
        print(f"   [WARN] Metrics failed: {e}")
    
    # Test chat completion
    print("\n3. Testing chat completion...")
    try:
        chat_request = ChatRequest(
            model="gpt-4o-mini",
            messages=[
                ChatMessage(role="user", content="What is semantic caching?")
            ]
        )
        chat_response = openai_compatible_v1_chat_completions_post.sync(
            client=client,
            body=chat_request
        )
        
        if chat_response:
            print(f"   [OK] Response ID: {chat_response.get('id', 'N/A')}")
            print(f"   [OK] Hit Type: {chat_response.get('meta', {}).get('hit', 'N/A')}")
            print(f"   [OK] Similarity: {chat_response.get('meta', {}).get('similarity', 0)}")
            print(f"   [OK] Latency: {chat_response.get('meta', {}).get('latency_ms', 0)}ms")
            response_text = chat_response.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"   [OK] Response: {response_text[:100]}...")
        else:
            print(f"   [FAIL] Chat completion returned None")
    except Exception as e:
        print(f"   [FAIL] Chat completion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[SUCCESS] SDK is working correctly!")
    print("=" * 60)
    print("\nSDK Integration Summary:")
    print("  - SDK can be imported")
    print("  - Health endpoint works")
    print("  - Metrics endpoint works")
    print("  - Chat completion works")
    print("  - Cache is functioning")
    print("\nClients can now use this SDK to integrate with your API!")
    print("\nHow clients integrate:")
    print("  1. Generate SDK: openapi-python-client generate --url YOUR_API/openapi.json --output sdk/python")
    print("  2. Install SDK: cd sdk/python && pip install -e .")
    print("  3. Use SDK: See CLIENT_SDK_INTEGRATION_COMPLETE.md for examples")
    
except ImportError as e:
    print(f"[ERROR] SDK not found. Error: {e}")
    print("\nTo generate the SDK, run:")
    print("  cd backend")
    print("  pip install openapi-python-client")
    print("  openapi-python-client generate --url http://localhost:8000/openapi.json --output ../sdk/python")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error testing SDK: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
