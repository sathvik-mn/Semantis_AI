# 🔍 How to Check if SDK is Working - Quick Guide

## Overview

This guide shows you how to verify that the SDK is working correctly and how clients can integrate it.

## ✅ Quick Check (1 Command)

```bash
cd D:\Semantis_AI
python test_sdk_working.py
```

**Expected Output:**
```
[OK] SDK imported successfully!

Testing SDK...

1. Testing health endpoint...
   [OK] Status: ok
   [OK] Service: semantic-cache
   [OK] Version: 0.1.0

2. Testing metrics endpoint...
   [OK] Total Requests: 50
   [OK] Hit Ratio: 60.0%
   [OK] Cache Entries: 20
   [OK] Semantic Hits: 14

3. Testing chat completion...
   [OK] Response ID: chatcmpl-...
   [OK] Hit Type: semantic
   [OK] Similarity: 0.85
   [OK] Latency: 120.5ms
   [OK] Response: Semantic caching is a technique...

============================================================
[SUCCESS] SDK is working correctly!
============================================================
```

## 📋 Step-by-Step Verification

### Step 1: Check SDK Exists

```bash
# Check if SDK directory exists
ls sdk/python/semantis_ai_semantic_cache_api_client

# Should show:
# - __init__.py
# - client.py
# - api/
# - models/
```

### Step 2: Test SDK Import

```bash
cd sdk/python
python -c "from semantis_ai_semantic_cache_api_client import Client; print('OK')"
```

**Expected:** `OK`

### Step 3: Test SDK with Backend

```bash
cd D:\Semantis_AI
python test_sdk_working.py
```

**Expected:** All tests pass

## 🚀 How Clients Integrate SDK

### For Clients: Step 1 - Generate SDK

```bash
# 1. Install SDK generator
pip install openapi-python-client

# 2. Generate SDK from your API
openapi-python-client generate \
  --url http://localhost:8000/openapi.json \
  --output ./sdk/python

# 3. Install SDK
cd sdk/python
pip install -e .
```

### For Clients: Step 2 - Use SDK in Code

```python
from semantis_ai_semantic_cache_api_client import Client
from semantis_ai_semantic_cache_api_client.api.default import (
    openai_compatible_v1_chat_completions_post
)
from semantis_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage

# Initialize client
client = Client(
    base_url="https://api.semantis.ai",  # Your API URL
    headers={
        "Authorization": "Bearer sc-your-tenant-api-key"
    }
)

# Make a cached chat completion
request = ChatRequest(
    model="gpt-4o-mini",
    messages=[ChatMessage(role="user", content="What is AI?")]
)

response = openai_compatible_v1_chat_completions_post.sync(
    client=client,
    body=request
)

# Get response
answer = response.choices[0].message.content
hit_type = response.meta.hit  # "exact", "semantic", or "miss"
similarity = response.meta.similarity
latency = response.meta.latency_ms

print(f"Answer: {answer}")
print(f"Cache hit: {hit_type}")
print(f"Similarity: {similarity}")
print(f"Latency: {latency}ms")
```

### For Clients: Step 3 - Replace OpenAI SDK

**Before (using OpenAI directly):**
```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}]
)
```

**After (using Semantis AI with caching):**
```python
from semantis_ai_semantic_cache_api_client import Client
from semantis_ai_semantic_cache_api_client.api.default import (
    openai_compatible_v1_chat_completions_post
)
from semantis_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage

client = Client(
    base_url="https://api.semantis.ai",
    headers={"Authorization": "Bearer sc-your-api-key"}
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
answer = response.choices[0].message.content
```

## 🔍 Verification Checklist

### SDK Generation
- [ ] SDK can be generated from OpenAPI spec
- [ ] SDK files exist in `sdk/python/`
- [ ] SDK can be imported without errors

### SDK Functionality
- [ ] Health endpoint works
- [ ] Metrics endpoint works
- [ ] Chat completion works
- [ ] Cache hits work (exact + semantic)
- [ ] Error handling works

### Client Integration
- [ ] Clients can generate SDK
- [ ] Clients can install SDK
- [ ] Clients can use SDK in their code
- [ ] SDK works as drop-in replacement for OpenAI

## 🛠️ Troubleshooting

### SDK Not Found

```bash
# Regenerate SDK
rm -rf sdk/python
pip install openapi-python-client
openapi-python-client generate \
  --url http://localhost:8000/openapi.json \
  --output sdk/python
```

### Import Errors

```bash
# Reinstall SDK
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

## 📊 What Clients Get

### Benefits
- ✅ **Automatic Caching**: Responses cached automatically
- ✅ **Faster Responses**: Cache hits return instantly
- ✅ **Cost Savings**: Fewer LLM API calls
- ✅ **Type-Safe**: Auto-generated from OpenAPI
- ✅ **OpenAI-Compatible**: Same response format

### SDK Features
- ✅ Health check endpoint
- ✅ Metrics endpoint
- ✅ Chat completion (with caching)
- ✅ Simple query endpoint
- ✅ Events endpoint
- ✅ Error handling
- ✅ Async support

## 🎯 Summary

### How to Check SDK is Working:

1. **Run test script**: `python test_sdk_working.py`
2. **Check output**: All tests should pass
3. **Verify integration**: SDK should work in client code

### How Clients Integrate:

1. **Generate SDK** from OpenAPI spec
2. **Install SDK** in their project
3. **Initialize client** with API key
4. **Use SDK** instead of OpenAI SDK
5. **Get automatic caching** - no code changes needed!

---

**That's how to check if the SDK is working and how clients integrate it!** 🚀

