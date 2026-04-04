# 🔌 Client SDK Integration Guide - Complete

## Overview

This guide explains how **your clients** integrate the Semantys AI Semantic Cache API into their applications using the generated SDK.

## 📦 Part 1: How Clients Get the SDK

### Step 1: Generate SDK from OpenAPI Spec

Clients generate the SDK from your OpenAPI specification:

```bash
# 1. Install SDK generator
pip install openapi-python-client

# 2. Generate SDK from your API
openapi-python-client generate \
  --url http://localhost:8000/openapi.json \
  --output ./sdk/python

# 3. Install the generated SDK
cd sdk/python
pip install -e .
```

**For Production:**
```bash
# Use your production API URL
openapi-python-client generate \
  --url https://api.semantys.ai/openapi.json \
  --output ./sdk/python
```

### Step 2: Install SDK in Client Project

```bash
# Option 1: Install from generated directory
cd sdk/python
pip install -e .

# Option 2: Install from PyPI (if you publish it)
pip install semantys-ai-semantic-cache-api-client
```

## 🚀 Part 2: How Clients Integrate SDK

### Example 1: Basic Integration (Python)

```python
# client_app.py
from semantys_ai_semantic_cache_api_client import Client
from semantys_ai_semantic_cache_api_client.api.default import (
    openai_compatible_v1_chat_completions_post
)
from semantys_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage
import os

# Initialize client with API key
client = Client(
    base_url="https://api.semantys.ai",  # Your API URL
    headers={
        "Authorization": f"Bearer {os.getenv('SEMANTYS_API_KEY')}"
    }
)

# Make a cached chat completion
def get_cached_response(user_query: str):
    request = ChatRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content=user_query)]
    )
    
    response = openai_compatible_v1_chat_completions_post.sync(
        client=client,
        body=request
    )
    
    return {
        "answer": response.choices[0].message.content,
        "hit_type": response.meta.hit,  # "exact", "semantic", or "miss"
        "similarity": response.meta.similarity,
        "latency_ms": response.meta.latency_ms
    }

# Use it
result = get_cached_response("What is AI?")
print(f"Answer: {result['answer']}")
print(f"Cache hit: {result['hit_type']}")
```

### Example 2: Replace OpenAI SDK (Drop-in Replacement)

If clients are already using OpenAI's Python SDK, they can easily switch:

```python
# Before (using OpenAI directly)
from openai import OpenAI
client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}]
)

# After (using Semantys AI with caching)
from semantys_ai_semantic_cache_api_client import Client
from semantys_ai_semantic_cache_api_client.api.default import (
    openai_compatible_v1_chat_completions_post
)
from semantys_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage

client = Client(
    base_url="https://api.semantys.ai",
    headers={"Authorization": f"Bearer {os.getenv('SEMANTYS_API_KEY')}"}
)

request = ChatRequest(
    model="gpt-4o-mini",
    messages=[ChatMessage(role="user", content="What is AI?")]
)

response = openai_compatible_v1_chat_completions_post.sync(
    client=client,
    body=request
)

# Same response format as OpenAI!
print(response.choices[0].message.content)
```

### Example 3: Integration in Flask/FastAPI App

```python
# app.py
from flask import Flask, request, jsonify
from semantys_ai_semantic_cache_api_client import Client
from semantys_ai_semantic_cache_api_client.api.default import (
    openai_compatible_v1_chat_completions_post
)
from semantys_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage

app = Flask(__name__)

# Initialize Semantys AI client
semantys_client = Client(
    base_url="https://api.semantys.ai",
    headers={
        "Authorization": f"Bearer {os.getenv('SEMANTYS_API_KEY')}"
    }
)

@app.route('/chat', methods=['POST'])
def chat():
    user_query = request.json.get('query')
    
    # Use Semantys AI SDK (with caching)
    request_obj = ChatRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content=user_query)]
    )
    
    response = openai_compatible_v1_chat_completions_post.sync(
        client=semantys_client,
        body=request_obj
    )
    
    return jsonify({
        "answer": response.choices[0].message.content,
        "cache_hit": response.meta.hit,
        "latency_ms": response.meta.latency_ms
    })

if __name__ == '__main__':
    app.run()
```

### Example 4: Async Integration

```python
# async_client.py
import asyncio
from semantys_ai_semantic_cache_api_client import Client
from semantys_ai_semantic_cache_api_client.api.default import (
    openai_compatible_v1_chat_completions_post
)
from semantys_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage

async def get_cached_response_async(user_query: str):
    client = Client(
        base_url="https://api.semantys.ai",
        headers={"Authorization": f"Bearer {os.getenv('SEMANTYS_API_KEY')}"}
    )
    
    request = ChatRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content=user_query)]
    )
    
    # Async call
    response = await openai_compatible_v1_chat_completions_post.asyncio(
        client=client,
        body=request
    )
    
    return response.choices[0].message.content

# Use it
result = asyncio.run(get_cached_response_async("What is AI?"))
print(result)
```

## 🔍 Part 3: How to Check if SDK is Working

### Test 1: Quick SDK Test

```bash
# Run the test script
cd backend
python test_sdk.py
```

**Expected Output:**
```
SDK imported successfully!

Testing SDK...

1. Testing health endpoint...
   Status: ok
   Service: semantic-cache
   Version: 0.1.0

2. Testing metrics endpoint...
   Total Requests: 10
   Hit Ratio: 0.6
   Cache Entries: 5

3. Testing chat completion...
   Response ID: chatcmpl-...
   Hit Type: semantic
   Similarity: 0.85
   Latency: 120.5ms
   Response: Artificial Intelligence (AI) refers to...

✅ SDK is working correctly!
```

### Test 2: Comprehensive Integration Test

```bash
# Run full integration test
python test_sdk_integration.py
```

**Expected Output:**
```
============================================================
SDK Integration Test Suite
============================================================

Testing SDK from client's perspective...
Backend URL: http://localhost:8000
API Key: Bearer sc-test-sdk-integration

============================================================
1. Testing Health Check
============================================================
✅ Service: semantic-cache
✅ Status: ok
✅ Version: 0.1.0

============================================================
2. Testing Chat Completion (with Caching)
============================================================

2.1. First Query (expected: miss)
   ✅ Hit type: miss
   ✅ Similarity: 0.0
   ✅ Latency: 3254.69ms
   ✅ Response: Artificial Intelligence (AI) refers to...

2.2. Second Query - Same (expected: exact hit)
   ✅ Hit type: exact
   ✅ Similarity: 1.0
   ✅ Latency: 0.02ms
   ✅ Cache working! Exact hit on second query.

2.3. Third Query - Similar (expected: semantic hit)
   ✅ Hit type: semantic
   ✅ Similarity: 0.85
   ✅ Latency: 120.5ms
   ✅ Semantic cache working! Similar query matched.

============================================================
3. Testing Metrics
============================================================
✅ Tenant: test-sdk-integration
✅ Total requests: 3
✅ Hits: 2
✅ Semantic hits: 1
✅ Misses: 1
✅ Hit ratio: 66.7%
✅ Cache entries: 1
✅ Similarity threshold: 0.72

============================================================
Test Summary
============================================================
[OK] PASS: Health Check
[OK] PASS: Chat Completion
[OK] PASS: Metrics
[OK] PASS: Error Handling

[SUCCESS] All SDK integration tests passed!
[SUCCESS] SDK is ready for client use!
```

### Test 3: Manual SDK Test

Create `test_sdk_manual.py`:

```python
import sys
import os

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sdk', 'python', 'src'))

from semantys_ai_semantic_cache_api_client import Client
from semantys_ai_semantic_cache_api_client.api.default import (
    health_health_get,
    openai_compatible_v1_chat_completions_post
)
from semantys_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage

# Test
client = Client(
    base_url="http://localhost:8000",
    headers={"Authorization": "Bearer sc-test-local"}
)

# 1. Health check
health = health_health_get.sync(client=client)
print(f"✅ Health: {health.status}")

# 2. Chat completion
request = ChatRequest(
    model="gpt-4o-mini",
    messages=[ChatMessage(role="user", content="Hello")]
)

response = openai_compatible_v1_chat_completions_post.sync(
    client=client,
    body=request
)

print(f"✅ Response: {response.choices[0].message.content[:50]}...")
print(f"✅ Hit type: {response.meta.hit}")
print(f"✅ SDK is working!")
```

Run it:
```bash
python test_sdk_manual.py
```

## 📋 Part 4: SDK Features for Clients

### What Clients Get

1. **Type-Safe Client**: Auto-generated from OpenAPI spec
2. **Authentication**: Built-in Bearer token support
3. **Error Handling**: Proper exception handling
4. **Cache Metadata**: Hit type, similarity, latency info
5. **OpenAI-Compatible**: Same response format as OpenAI
6. **Async Support**: Both sync and async methods

### SDK Methods Available

```python
# Health check
health_health_get.sync(client=client)

# Get metrics
get_metrics_metrics_get.sync(client=client)

# Chat completion (with caching)
openai_compatible_v1_chat_completions_post.sync(client=client, body=request)

# Simple query
simple_query_query_get.sync(client=client, prompt="...")

# Get events
get_events_events_get.sync(client=client)
```

## 🎯 Part 5: Client Integration Checklist

### For Clients to Integrate:

- [ ] Generate SDK from OpenAPI spec
- [ ] Install SDK in their project
- [ ] Get API key from you
- [ ] Initialize client with API key
- [ ] Replace OpenAI calls with Semantys AI SDK
- [ ] Test integration
- [ ] Monitor cache hit rates
- [ ] Handle errors gracefully

### For You to Provide:

- [ ] OpenAPI spec URL (`/openapi.json`)
- [ ] API base URL (`https://api.semantys.ai`)
- [ ] API keys for clients
- [ ] SDK generation instructions
- [ ] Integration examples
- [ ] Documentation

## 🛠️ Part 6: Troubleshooting

### SDK Not Found

```bash
# Regenerate SDK
rm -rf sdk/python
openapi-python-client generate \
  --url http://localhost:8000/openapi.json \
  --output sdk/python

# Reinstall
cd sdk/python
pip install -e .
```

### Import Errors

```bash
# Check SDK is installed
pip list | grep semantys

# Reinstall
cd sdk/python
pip install -e . --force-reinstall
```

### Connection Errors

```bash
# Check backend is running
curl http://localhost:8000/health

# Check API key format
# Should be: Bearer sc-{tenant}-{anything}
```

## 📊 Part 7: How to Verify SDK is Working

### Quick Verification

```bash
# 1. Check SDK exists
ls sdk/python/semantys_ai_semantic_cache_api_client

# 2. Test import
python -c "from semantys_ai_semantic_cache_api_client import Client; print('OK')"

# 3. Run test
python test_sdk.py
```

### Full Verification

```bash
# Run comprehensive test
python test_sdk_integration.py
```

**Success Indicators:**
- ✅ SDK imports without errors
- ✅ Health check works
- ✅ Chat completion works
- ✅ Cache hits work (exact + semantic)
- ✅ Metrics endpoint works
- ✅ Error handling works

## 🎉 Summary

### How Clients Integrate:

1. **Generate SDK** from your OpenAPI spec
2. **Install SDK** in their project
3. **Initialize client** with their API key
4. **Replace OpenAI calls** with Semantys AI SDK
5. **Get automatic caching** - no code changes needed!

### How to Check if SDK Works:

1. **Run test script**: `python test_sdk.py`
2. **Run integration test**: `python test_sdk_integration.py`
3. **Manual test**: Create simple script using SDK

### Benefits for Clients:

- ✅ **Drop-in replacement** for OpenAI SDK
- ✅ **Automatic caching** - faster responses
- ✅ **Cost savings** - fewer LLM calls
- ✅ **Type-safe** - auto-generated from OpenAPI
- ✅ **Same format** - OpenAI-compatible responses

---

**That's how clients integrate and use the SDK!** 🚀

