# SDK and Cache Warmup Guide

## 🎯 Overview

This guide covers:
1. **SDK Generation and Testing** - How to generate and use the Python SDK
2. **Cache Warmup** - How to pre-populate the cache to avoid LLM calls on first requests
3. **Handling Random Domain Questions** - Understanding cache behavior

## 1. SDK Generation and Usage

### Generate Python SDK

The OpenAPI specification is available at `http://localhost:8000/openapi.json`. You can generate SDKs for various languages.

#### Python SDK

```bash
cd backend
python -m pip install openapi-python-client
python -m openapi_python_client generate --path openapi.json --output-path ../sdk/python --overwrite
```

#### Using the Generated SDK

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
        "Authorization": "Bearer sc-test-local"
    }
)

# Test health
health = health_health_get.sync(client=client)
print(f"Status: {health.status}")

# Get metrics
metrics = get_metrics_metrics_get.sync(client=client)
print(f"Hit Ratio: {metrics.hit_ratio}")

# Chat completion
request = ChatRequest(
    model="gpt-4o-mini",
    messages=[ChatMessage(role="user", content="What is AI?")]
)
response = openai_compatible_v1_chat_completions_post.sync(
    client=client,
    body=request
)
print(f"Response: {response.choices[0].message.content}")
```

#### Test the SDK

```bash
python test_sdk.py
```

### Generate Other Language SDKs

#### TypeScript/JavaScript
```bash
# Using openapi-generator
npm install @openapitools/openapi-generator-cli -g
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g typescript-axios -o sdk/typescript
```

#### Go
```bash
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g go -o sdk/go
```

#### Java
```bash
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g java -o sdk/java
```

## 2. Cache Warmup (Pre-population)

### Problem
When a user asks a random domain question for the first time, it will always result in a cache miss and an LLM call, which is slow and costs money.

### Solution: Cache Warmup
Pre-populate the cache with common queries so they're already cached when users ask them.

### Using the Warmup Script

#### Basic Usage
```bash
cd backend
python cache_warmup.py --api-key sc-test-local --queries 10
```

#### Using a Custom Query File
```bash
python cache_warmup.py --api-key sc-test-local --file warmup_queries.json
```

#### Options
- `--api-key`: API key (default: `sc-test-local`)
- `--url`: Backend URL (default: `http://localhost:8000`)
- `--file`: JSON file with queries
- `--queries`: Number of default queries to use (if not using file)

### Query File Format

Create a JSON file (`warmup_queries.json`):

```json
[
  {
    "prompt": "What is artificial intelligence?",
    "model": "gpt-4o-mini"
  },
  {
    "prompt": "Explain machine learning",
    "model": "gpt-4o-mini"
  }
]
```

### Example: Warmup Common Queries

```bash
# Warm up with 15 common queries
python cache_warmup.py --api-key sc-test-local --queries 15

# Warm up with custom queries from file
python cache_warmup.py --api-key sc-test-local --file my_queries.json
```

### Results
The script will:
1. Process each query
2. Make API calls to populate the cache
3. Show progress and results
4. Save results to `warmup_results.json`

### Benefits
- ✅ First user request hits the cache (fast response)
- ✅ Reduces LLM API costs
- ✅ Improves user experience (faster responses)
- ✅ Better cache hit ratios from the start

## 3. Handling Random Domain Questions

### How It Works

#### First Request (Cache Miss)
1. User asks: "What is quantum computing?"
2. Cache check: Not found (exact match)
3. Semantic search: No similar queries found
4. **Result: Cache miss → LLM call** (slow, costs money)

#### Second Request (Cache Hit)
1. User asks: "What is quantum computing?" (exact same)
2. Cache check: Found in exact cache
3. **Result: Exact hit → Instant response** (fast, free)

#### Similar Request (Semantic Hit)
1. User asks: "Explain quantum computing" (similar to cached query)
2. Cache check: Not found (exact match)
3. Semantic search: Found similar query (similarity > 0.83)
4. **Result: Semantic hit → Fast response** (fast, free)

### Strategies for Random Domains

#### 1. Domain-Specific Warmup
Pre-populate cache with domain-specific queries:

```bash
# Create domain-specific queries
cat > healthcare_queries.json << EOF
[
  {"prompt": "What is diabetes?", "model": "gpt-4o-mini"},
  {"prompt": "Explain heart disease", "model": "gpt-4o-mini"},
  {"prompt": "What are symptoms of flu?", "model": "gpt-4o-mini"}
]
EOF

# Warm up healthcare domain
python cache_warmup.py --file healthcare_queries.json
```

#### 2. Batch Warmup on Startup
Add warmup to your application startup:

```python
# In your application startup
from backend.cache_warmup import warmup_cache, COMMON_QUERIES

# Warm up cache on startup
warmup_cache(COMMON_QUERIES[:20], api_key="sc-your-tenant-key")
```

#### 3. Scheduled Warmup
Run warmup periodically to refresh cache:

```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/backend && python cache_warmup.py --queries 20
```

#### 4. User-Driven Warmup
Warm up based on user behavior:

```python
# Track common queries
common_queries = get_most_common_queries_from_logs()

# Warm up those queries
warmup_cache(common_queries, api_key="sc-your-tenant-key")
```

## 4. Best Practices

### Cache Warmup
1. **Identify Common Queries**: Analyze user logs to find frequent questions
2. **Domain-Specific**: Warm up queries relevant to your domain
3. **Regular Updates**: Refresh cache periodically with new common queries
4. **Monitor Performance**: Track cache hit ratios after warmup

### SDK Usage
1. **Error Handling**: Always handle API errors gracefully
2. **Rate Limiting**: Respect rate limits when making multiple requests
3. **Authentication**: Store API keys securely (environment variables)
4. **Connection Pooling**: Reuse client instances for better performance

### Cache Management
1. **TTL Settings**: Adjust TTL based on your use case
2. **Cache Size**: Monitor cache size and implement eviction if needed
3. **Similarity Threshold**: Tune threshold based on your domain (default: 0.83)
4. **Metrics Monitoring**: Regularly check cache metrics for optimization

## 5. Testing

### Test SDK
```bash
python test_sdk.py
```

### Test Cache Warmup
```bash
# Warm up cache
python cache_warmup.py --queries 5

# Check metrics
curl -H "Authorization: Bearer sc-test-local" http://localhost:8000/metrics

# Test a warmed query (should be fast)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sc-test-local" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "What is artificial intelligence?"}]
  }'
```

## 6. Summary

### SDK
- ✅ OpenAPI spec available at `/openapi.json`
- ✅ Generate SDKs for any language
- ✅ Python SDK tested and working
- ✅ Type-safe client with authentication

### Cache Warmup
- ✅ Pre-populate cache with common queries
- ✅ Avoid LLM calls on first requests
- ✅ Improve cache hit ratios
- ✅ Reduce costs and latency

### Random Domain Questions
- ✅ First request: Cache miss (expected)
- ✅ Second request: Cache hit (fast)
- ✅ Similar requests: Semantic hit (fast)
- ✅ Use warmup to pre-populate common queries

## 7. Next Steps

1. **Generate SDK** for your preferred language
2. **Create query files** for your domain
3. **Run warmup** before going to production
4. **Monitor metrics** to optimize cache performance
5. **Update queries** based on user behavior

---

**Need Help?**
- Check `test_sdk.py` for SDK usage examples
- Check `cache_warmup.py` for warmup script
- Check `warmup_queries.json` for query format examples

