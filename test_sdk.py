"""
Test script for the generated Python SDK
"""
import sys
import os

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sdk', 'python', 'src'))

try:
    from semantis_ai_semantic_cache_api import Client
    from semantis_ai_semantic_cache_api.api.default import health_health_get, get_metrics_metrics_get, openai_compatible_v1_chat_completions_post
    from semantis_ai_semantic_cache_api.models import ChatRequest, ChatMessage
    from semantis_ai_semantic_cache_api.types import Response
    
    print("SDK imported successfully!")
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
    health_response = health_health_get.sync(client=client)
    print(f"   Status: {health_response.status}")
    print(f"   Service: {health_response.service}")
    print(f"   Version: {health_response.version}")
    
    # Test metrics endpoint
    print("\n2. Testing metrics endpoint...")
    metrics_response = get_metrics_metrics_get.sync(client=client)
    print(f"   Total Requests: {metrics_response.total_requests}")
    print(f"   Hit Ratio: {metrics_response.hit_ratio}")
    print(f"   Cache Entries: {metrics_response.entries}")
    
    # Test chat completion
    print("\n3. Testing chat completion...")
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
    print(f"   Response ID: {chat_response.id}")
    print(f"   Hit Type: {chat_response.meta.hit}")
    print(f"   Similarity: {chat_response.meta.similarity}")
    print(f"   Latency: {chat_response.meta.latency_ms}ms")
    print(f"   Response: {chat_response.choices[0].message.content[:100]}...")
    
    print("\n✅ SDK is working correctly!")
    
except ImportError as e:
    print(f"❌ SDK not found. Error: {e}")
    print("\nTo generate the SDK, run:")
    print("  cd backend")
    print("  python -m openapi_python_client generate --path openapi.json --output-path ../sdk/python --overwrite")
except Exception as e:
    print(f"[ERROR] Error testing SDK: {e}")
    import traceback
    traceback.print_exc()

