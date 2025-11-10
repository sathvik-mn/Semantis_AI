# Semantis Cache - Python SDK

Production-ready Python SDK for Semantis AI Semantic Caching.

## Installation

```bash
pip install semantis-cache
```

## Quick Start

### Simple Query (Recommended)

```python
from semantis_cache import SemanticCache

# Initialize client (caching is automatic!)
cache = SemanticCache(api_key="sc-your-key")

# Simple query method - returns answer with cache metadata
response = cache.query("What is our refund policy?")
print(response.answer)
print(f"Cache hit: {response.cache_hit}")  # 'exact', 'semantic', or 'miss'
print(f"Similarity: {response.similarity}")
print(f"Latency: {response.latency_ms}ms")
```

### OpenAI-Compatible API

```python
from semantis_cache import SemanticCache

cache = SemanticCache(api_key="sc-your-key")

# Use just like OpenAI - caching happens automatically
response = cache.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}]
)

print(response.choices[0].message.content)
print(f"Cache hit: {response.cache_hit}")
```

### OpenAI Proxy (Drop-in Replacement)

```python
from semantis_cache.openai_proxy import ChatCompletion

# Drop-in replacement for OpenAI ChatCompletion
response = ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}]
)

print(response.choices[0].message.content)
print(f"Cache hit: {response.cache_hit}")  # Bonus: cache metadata!
```

## Features

- ✅ **Simple API**: `cache.query("prompt")` - easiest way to use
- ✅ **OpenAI-Compatible**: Drop-in replacement for OpenAI SDK
- ✅ **Automatic caching** - No code changes needed
- ✅ **Semantic matching** - Similar queries match automatically
- ✅ **Fast responses** - Cache hits return instantly
- ✅ **Cost savings** - Fewer LLM API calls
- ✅ **Cache metadata** - See cache hits, similarity, latency

## Usage

### Environment Variables

```bash
export SEMANTIS_API_KEY="sc-your-key"
export SEMANTIS_API_URL="https://api.semantis.ai"  # Optional
```

```python
from semantis_cache import SemanticCache

# Uses SEMANTIS_API_KEY from environment
cache = SemanticCache()
```

### Cache Metadata

```python
response = cache.query("What is AI?")

# Access cache information
print(response.answer)          # Answer string
print(response.cache_hit)       # 'exact', 'semantic', or 'miss'
print(response.similarity)      # Similarity score (for semantic hits)
print(response.latency_ms)      # Response latency in milliseconds
print(response.metrics)         # Cache metrics (hit ratio, etc.)
```

## Migration from OpenAI

### Before (OpenAI)
```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}]
)
```

### After (Semantis Cache)
```python
from semantis_cache import SemanticCache

cache = SemanticCache(api_key="sc-your-key")
response = cache.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}]
)
# Same API, automatic caching!
```

### Or Use Proxy
```python
from semantis_cache.openai_proxy import ChatCompletion

# Exact same API as OpenAI
response = ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}]
)
```

## Requirements

- Python 3.10+
- httpx
- attrs
- python-dateutil

## License

MIT

## Support

- Documentation: https://docs.semantis.ai
- Issues: https://github.com/semantis-ai/semantis-cache-python/issues
