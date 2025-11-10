# 🔌 SDK Integration Guide - For Clients

## Overview

The Semantis AI Semantic Cache API provides an **OpenAPI-compatible SDK** that clients can use to integrate semantic caching into their applications. This guide explains how to generate, install, and use the SDK.

## 📦 SDK Generation

### Step 1: Generate OpenAPI Specification

The SDK is generated from the OpenAPI specification. First, ensure the backend is running:

```bash
cd backend
python semantic_cache_server.py
```

The OpenAPI spec is automatically available at:
- **JSON**: http://localhost:8000/openapi.json
- **Interactive Docs**: http://localhost:8000/docs

### Step 2: Generate Python SDK

```bash
# Install SDK generator
pip install openapi-python-client

# Generate SDK from OpenAPI spec
openapi-python-client generate --url http://localhost:8000/openapi.json --output sdk/python
```

This creates a Python SDK in `sdk/python/` directory.

### Step 3: Install SDK

```bash
cd sdk/python
pip install -e .
```

Or install from the generated package:

```bash
pip install -e sdk/python
```

## 🚀 Client Integration Examples

### Python Client Example

```python
from semantis_ai_semantic_cache_api import Client
from semantis_ai_semantic_cache_api.api.default import (
    health_health_get,
    get_metrics_metrics_get,
    openai_compatible_v1_chat_completions_post
)
from semantis_ai_semantic_cache_api.models import ChatRequest, ChatMessage

# Initialize client
client = Client(
    base_url="http://localhost:8000",
    headers={
        "Authorization": "Bearer sc-your-tenant-api-key"
    }
)

# 1. Check health
health = health_health_get.sync(client=client)
print(f"Service: {health.service}, Version: {health.version}")

# 2. Make a chat completion (with caching)
chat_request = ChatRequest(
    model="gpt-4o-mini",
    messages=[
        ChatMessage(role="user", content="What is semantic caching?")
    ],
    temperature=0.2,
    ttl_seconds=604800  # 7 days
)

response = openai_compatible_v1_chat_completions_post.sync(
    client=client,
    body=chat_request
)

print(f"Response: {response.choices[0].message.content}")
print(f"Hit type: {response.meta.hit}")  # exact, semantic, or miss
print(f"Similarity: {response.meta.similarity}")
print(f"Latency: {response.meta.latency_ms}ms")

# 3. Get metrics
metrics = get_metrics_metrics_get.sync(client=client)
print(f"Hit ratio: {metrics.hit_ratio}")
print(f"Cache entries: {metrics.entries}")
```

### JavaScript/TypeScript Client Example

```bash
# Generate JavaScript SDK
npx @openapitools/openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o sdk/javascript
```

```typescript
import { Configuration, DefaultApi } from './sdk/javascript';

const config = new Configuration({
  basePath: 'http://localhost:8000',
  accessToken: 'sc-your-tenant-api-key',
});

const api = new DefaultApi(config);

// Make a chat completion
const response = await api.openaiCompatibleV1ChatCompletionsPost({
  model: 'gpt-4o-mini',
  messages: [
    { role: 'user', content: 'What is semantic caching?' }
  ],
});

console.log('Response:', response.data.choices[0].message.content);
console.log('Hit type:', response.data.meta.hit);
console.log('Similarity:', response.data.meta.similarity);
```

### cURL Example (No SDK)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sc-your-tenant-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "What is semantic caching?"}
    ]
  }'
```

## 🔍 How to Verify SDK is Working

### Test 1: Generate SDK

```bash
# 1. Start backend
cd backend
python semantic_cache_server.py

# 2. Generate SDK
pip install openapi-python-client
openapi-python-client generate --url http://localhost:8000/openapi.json --output sdk/python

# 3. Verify SDK generated
ls sdk/python/src/semantis_ai_semantic_cache_api
```

### Test 2: Install and Import SDK

```bash
cd sdk/python
pip install -e .

# Test import
python -c "from semantis_ai_semantic_cache_api import Client; print('SDK imported successfully!')"
```

### Test 3: Run SDK Test Script

```bash
cd D:\Semantis_AI
python test_sdk.py
```

Expected output:
```
SDK imported successfully!
✅ Health endpoint works
✅ Metrics endpoint works
✅ Chat completion works
```

### Test 4: Manual SDK Test

Create `test_sdk_manual.py`:

```python
from semantis_ai_semantic_cache_api import Client
from semantis_ai_semantic_cache_api.api.default import (
    health_health_get,
    openai_compatible_v1_chat_completions_post
)
from semantis_ai_semantic_cache_api.models import ChatRequest, ChatMessage

# Initialize client
client = Client(
    base_url="http://localhost:8000",
    headers={"Authorization": "Bearer sc-test-local"}
)

# Test health
print("1. Testing health endpoint...")
health = health_health_get.sync(client=client)
print(f"   ✅ Service: {health.service}")
print(f"   ✅ Version: {health.version}")

# Test chat completion
print("\n2. Testing chat completion...")
chat_request = ChatRequest(
    model="gpt-4o-mini",
    messages=[ChatMessage(role="user", content="Hello, what is AI?")]
)

response = openai_compatible_v1_chat_completions_post.sync(
    client=client,
    body=chat_request
)

print(f"   ✅ Response received")
print(f"   ✅ Hit type: {response.meta.hit}")
print(f"   ✅ Similarity: {response.meta.similarity}")
print(f"   ✅ Latency: {response.meta.latency_ms}ms")
print(f"   ✅ Content: {response.choices[0].message.content[:50]}...")

print("\n✅ SDK is working correctly!")
```

Run it:
```bash
python test_sdk_manual.py
```

## 📋 Integration Checklist

### For Clients

- [ ] Backend API is running
- [ ] OpenAPI spec is accessible
- [ ] SDK generated successfully
- [ ] SDK installed in client project
- [ ] API key obtained
- [ ] Client code written
- [ ] SDK tested with sample queries
- [ ] Integration tested in development
- [ ] Error handling implemented
- [ ] Monitoring/logging added

### For Service Providers

- [ ] OpenAPI spec is up-to-date
- [ ] API endpoints are documented
- [ ] Authentication is working
- [ ] SDK generation works
- [ ] Example code provided
- [ ] Documentation is clear
- [ ] Support channels available

## 🛠️ SDK Features

### Supported Operations

1. **Health Check** - Verify service status
2. **Chat Completions** - OpenAI-compatible API
3. **Metrics** - Get cache performance metrics
4. **Query** - Simple query endpoint
5. **Events** - Get cache events

### SDK Benefits

- ✅ **Type Safety** - TypeScript/Python type hints
- ✅ **Auto-completion** - IDE support
- ✅ **Error Handling** - Built-in error types
- ✅ **Documentation** - Auto-generated docs
- ✅ **Validation** - Request/response validation

## 🔧 Troubleshooting

### SDK Generation Fails

```bash
# Check OpenAPI spec is accessible
curl http://localhost:8000/openapi.json

# Regenerate SDK
rm -rf sdk/python
openapi-python-client generate --url http://localhost:8000/openapi.json --output sdk/python
```

### SDK Import Fails

```bash
# Reinstall SDK
cd sdk/python
pip uninstall semantis-ai-semantic-cache-api
pip install -e .
```

### Authentication Issues

```bash
# Verify API key format
# Should be: Bearer sc-{tenant}-{anything}

# Test with curl
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sc-test-local" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"test"}]}'
```

## 📚 Additional Resources

### OpenAPI Tools

- **Python**: `openapi-python-client`
- **TypeScript**: `@openapitools/openapi-generator-cli`
- **Go**: `openapi-generator`
- **Java**: `openapi-generator`

### Documentation

- **API Docs**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Backend README**: `backend/README.md`

## 🎯 Quick Start for Clients

1. **Get API Key**: Generate or obtain API key
2. **Generate SDK**: Use OpenAPI generator
3. **Install SDK**: Install in your project
4. **Initialize Client**: Create client instance
5. **Make Requests**: Use SDK methods
6. **Handle Responses**: Process cache hits/misses

## ✅ Verification Steps

1. ✅ Backend running
2. ✅ OpenAPI spec accessible
3. ✅ SDK generated
4. ✅ SDK installed
5. ✅ SDK imported
6. ✅ Health check works
7. ✅ Chat completion works
8. ✅ Metrics retrieval works

---

**That's it! Your clients can now integrate the semantic cache API into their services using the SDK!** 🚀

