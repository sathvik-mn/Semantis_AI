# ✅ SDK Verification Guide - How to Check if SDK is Working

## Quick Check

### Step 1: Verify SDK Exists

```bash
# Check if SDK is generated
ls sdk/python/src/semantis_ai_semantic_cache_api

# Should see:
# - client.py
# - api/
# - models/
```

### Step 2: Test SDK Import

```python
# Test import
python -c "from semantis_ai_semantic_cache_api import Client; print('SDK imported successfully!')"
```

### Step 3: Run Test Script

```bash
# Run comprehensive test
python test_sdk_integration.py
```

## Detailed Verification

### 1. Check Backend is Running

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"ok","service":"semantic-cache","version":"0.1.0"}
```

### 2. Check OpenAPI Spec

```bash
# Get OpenAPI spec
curl http://localhost:8000/openapi.json

# Should return JSON with API specification
```

### 3. Generate SDK (if not exists)

```bash
# Install generator
pip install openapi-python-client

# Generate SDK
openapi-python-client generate \
  --url http://localhost:8000/openapi.json \
  --output sdk/python
```

### 4. Install SDK

```bash
cd sdk/python
pip install -e .
```

### 5. Test SDK

```bash
# Run test
python test_sdk.py
```

Expected output:
```
SDK imported successfully!
✅ Health endpoint works
✅ Metrics endpoint works
✅ Chat completion works
```

## Integration Test

### Run Full Integration Test

```bash
python test_sdk_integration.py
```

This tests:
1. ✅ Health check
2. ✅ Chat completion (first query - miss)
3. ✅ Chat completion (second query - exact hit)
4. ✅ Chat completion (similar query - semantic hit)
5. ✅ Metrics retrieval
6. ✅ Error handling

## Client Integration Verification

### For Your Clients

Clients should verify:

1. **SDK Generation**
   ```bash
   openapi-python-client generate --url YOUR_API_URL/openapi.json --output sdk/python
   ```

2. **SDK Installation**
   ```bash
   cd sdk/python
   pip install -e .
   ```

3. **SDK Import**
   ```python
   from semantis_ai_semantic_cache_api import Client
   ```

4. **Health Check**
   ```python
   from semantis_ai_semantic_cache_api.api.default import health_health_get
   health = health_health_get.sync(client=client)
   assert health.service == "semantic-cache"
   ```

5. **Chat Completion**
   ```python
   from semantis_ai_semantic_cache_api.api.default import openai_compatible_v1_chat_completions_post
   response = openai_compatible_v1_chat_completions_post.sync(client=client, body=request)
   assert response.meta.hit in ["exact", "semantic", "miss"]
   ```

## Troubleshooting

### SDK Not Found

```bash
# Regenerate SDK
rm -rf sdk/python
openapi-python-client generate --url http://localhost:8000/openapi.json --output sdk/python
```

### Import Errors

```bash
# Reinstall SDK
cd sdk/python
pip uninstall semantis-ai-semantic-cache-api
pip install -e .
```

### Authentication Errors

```bash
# Verify API key format
# Should be: Bearer sc-{tenant}-{anything}

# Test with curl
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sc-test-local" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"test"}]}'
```

## Success Criteria

✅ **SDK Generated**: SDK files exist in `sdk/python/`
✅ **SDK Installed**: Can import SDK without errors
✅ **Health Check Works**: Can call health endpoint
✅ **Chat Completion Works**: Can make chat requests
✅ **Cache Works**: See cache hits on repeated queries
✅ **Metrics Work**: Can retrieve cache metrics
✅ **Error Handling Works**: Errors are caught and handled

## Quick Verification Command

```bash
# One-line verification
python -c "
from semantis_ai_semantic_cache_api import Client
from semantis_ai_semantic_cache_api.api.default import health_health_get
client = Client(base_url='http://localhost:8000')
health = health_health_get.sync(client=client)
print(f'[OK] SDK working! Service: {health.service}')
"
```

---

**If all checks pass, the SDK is ready for client use!** 🚀

