# 🔌 Client SDK Integration Guide

## Overview

This guide explains how **your clients** can integrate the Semantis AI Semantic Cache API into their applications using the SDK.

## 📦 Step 1: Generate the SDK

### For Python Clients

```bash
# 1. Install SDK generator
pip install openapi-python-client

# 2. Generate SDK from OpenAPI spec
openapi-python-client generate \
  --url http://localhost:8000/openapi.json \
  --output ./sdk/python

# 3. Install the SDK
cd sdk/python
pip install -e .
```

### For TypeScript/JavaScript Clients

```bash
# 1. Install SDK generator
npm install -g @openapitools/openapi-generator-cli

# 2. Generate SDK
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o ./sdk/typescript
```

## 🚀 Step 2: Client Integration Examples

### Python Integration

```python
from semantis_ai_semantic_cache_api import Client
from semantis_ai_semantic_cache_api.api.default import openai_compatible_v1_chat_completions_post
from semantis_ai_semantic_cache_api.models import ChatRequest, ChatMessage

# Initialize client with API key
client = Client(
    base_url="https://api.semantis.ai",  # Your API URL
    headers={
        "Authorization": "Bearer sc-your-tenant-api-key"
    }
)

# Make a cached chat completion
def get_cached_response(user_query: str):
    chat_request = ChatRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content=user_query)],
        temperature=0.2,
        ttl_seconds=604800  # 7 days
    )
    
    response = openai_compatible_v1_chat_completions_post.sync(
        client=client,
        body=chat_request
    )
    
    # Check cache performance
    hit_type = response.meta.hit  # "exact", "semantic", or "miss"
    similarity = response.meta.similarity
    latency = response.meta.latency_ms
    
    return {
        "content": response.choices[0].message.content,
        "cached": hit_type != "miss",
        "hit_type": hit_type,
        "similarity": similarity,
        "latency_ms": latency
    }

# Use it
result = get_cached_response("What is semantic caching?")
print(f"Response: {result['content']}")
print(f"Cached: {result['cached']}")
print(f"Latency: {result['latency_ms']}ms")
```

### TypeScript Integration

```typescript
import { Configuration, DefaultApi, ChatRequest, ChatMessage } from './sdk/typescript';

// Initialize client
const config = new Configuration({
  basePath: 'https://api.semantis.ai',
  accessToken: 'sc-your-tenant-api-key',
});

const api = new DefaultApi(config);

// Make a cached chat completion
async function getCachedResponse(userQuery: string) {
  const request: ChatRequest = {
    model: 'gpt-4o-mini',
    messages: [
      { role: 'user', content: userQuery }
    ],
    temperature: 0.2,
    ttlSeconds: 604800
  };
  
  const response = await api.openaiCompatibleV1ChatCompletionsPost(request);
  
  return {
    content: response.data.choices[0].message.content,
    cached: response.data.meta.hit !== 'miss',
    hitType: response.data.meta.hit,
    similarity: response.data.meta.similarity,
    latencyMs: response.data.meta.latencyMs
  };
}

// Use it
const result = await getCachedResponse('What is semantic caching?');
console.log(`Response: ${result.content}`);
console.log(`Cached: ${result.cached}`);
console.log(`Latency: ${result.latencyMs}ms`);
```

### Integration with Existing OpenAI Code

If clients are already using OpenAI's Python SDK, they can easily switch:

```python
# Before (direct OpenAI)
from openai import OpenAI
client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}]
)

# After (with semantic cache)
from semantis_ai_semantic_cache_api import Client
from semantis_ai_semantic_cache_api.api.default import openai_compatible_v1_chat_completions_post
from semantis_ai_semantic_cache_api.models import ChatRequest, ChatMessage

cache_client = Client(
    base_url="https://api.semantis.ai",
    headers={"Authorization": "Bearer sc-your-tenant-api-key"}
)

# Same interface, but with caching!
response = openai_compatible_v1_chat_completions_post.sync(
    client=cache_client,
    body=ChatRequest(
        model="gpt-4o-mini",
        messages=[ChatMessage(role="user", content="What is AI?")]
    )
)
```

## 🔍 Step 3: Verify SDK is Working

### Test Script for Clients

Create `test_client_integration.py`:

```python
from semantis_ai_semantic_cache_api import Client
from semantis_ai_semantic_cache_api.api.default import (
    health_health_get,
    openai_compatible_v1_chat_completions_post
)
from semantis_ai_semantic_cache_api.models import ChatRequest, ChatMessage

# Initialize client
client = Client(
    base_url="http://localhost:8000",  # Or your API URL
    headers={"Authorization": "Bearer sc-your-tenant-api-key"}
)

# Test 1: Health check
print("1. Testing health check...")
health = health_health_get.sync(client=client)
print(f"   [OK] Service: {health.service}")
print(f"   [OK] Version: {health.version}")

# Test 2: Chat completion
print("\n2. Testing chat completion...")
request = ChatRequest(
    model="gpt-4o-mini",
    messages=[ChatMessage(role="user", content="Hello, what is AI?")]
)

response = openai_compatible_v1_chat_completions_post.sync(
    client=client,
    body=request
)

print(f"   [OK] Response received")
print(f"   [OK] Hit type: {response.meta.hit}")
print(f"   [OK] Similarity: {response.meta.similarity}")
print(f"   [OK] Latency: {response.meta.latency_ms}ms")
print(f"   [OK] Content: {response.choices[0].message.content[:50]}...")

print("\n[SUCCESS] SDK integration successful!")
```

Run it:
```bash
python test_client_integration.py
```

## 📊 Step 4: Monitor Cache Performance

Clients can monitor cache performance:

```python
from semantis_ai_semantic_cache_api.api.default import get_metrics_metrics_get

# Get metrics
metrics = get_metrics_metrics_get.sync(client=client)

print(f"Hit ratio: {metrics.hit_ratio:.1%}")
print(f"Cache entries: {metrics.entries}")
print(f"Semantic hits: {metrics.semantic_hits}")
print(f"Average latency: {metrics.avg_latency_ms}ms")
```

## 🛠️ Step 5: Error Handling

```python
from semantis_ai_semantic_cache_api.exceptions import ApiException

try:
    response = openai_compatible_v1_chat_completions_post.sync(
        client=client,
        body=request
    )
except ApiException as e:
    if e.status == 401:
        print("[ERROR] Invalid API key")
    elif e.status == 429:
        print("[ERROR] Rate limit exceeded")
    else:
        print(f"[ERROR] Error: {e.status} - {e.reason}")
```

## ✅ How to Check if SDK is Working

### Method 1: Run Test Script

```bash
# Test the SDK
python test_sdk.py
```

Expected output:
```
SDK imported successfully!
✅ Health endpoint works
✅ Metrics endpoint works
✅ Chat completion works
```

### Method 2: Run Integration Test

```bash
# Run comprehensive integration test
python test_sdk_integration.py
```

This tests:
- Health check
- Chat completion (with caching)
- Metrics retrieval
- Error handling

### Method 3: Manual Test

```python
from semantis_ai_semantic_cache_api import Client
from semantis_ai_semantic_cache_api.api.default import health_health_get

client = Client(base_url="http://localhost:8000")
health = health_health_get.sync(client=client)
print(f"Service: {health.service}")  # Should print: semantic-cache
```

## 📋 Integration Checklist

### For Service Providers (You)

- [ ] Backend API is running
- [ ] OpenAPI spec is accessible at `/openapi.json`
- [ ] API documentation is available at `/docs`
- [ ] SDK can be generated from OpenAPI spec
- [ ] Example code is provided
- [ ] API keys can be generated
- [ ] Authentication is working
- [ ] Caching is working (exact + semantic)

### For Clients

- [ ] SDK generated successfully
- [ ] SDK installed in project
- [ ] API key obtained
- [ ] Client code written
- [ ] Health check works
- [ ] Chat completion works
- [ ] Cache hits are occurring
- [ ] Metrics can be retrieved
- [ ] Error handling implemented

## 🎯 Quick Start for Clients

1. **Get API Key**: `python api_key_generator.py --tenant client-name --save`
2. **Generate SDK**: `openapi-python-client generate --url http://localhost:8000/openapi.json --output sdk/python`
3. **Install SDK**: `cd sdk/python && pip install -e .`
4. **Use SDK**: See examples above
5. **Test**: Run `test_client_integration.py`

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **SDK Guide**: This document
- **Integration Examples**: `test_sdk_integration.py`

---

**That's how clients integrate and use the SDK!** 🚀

