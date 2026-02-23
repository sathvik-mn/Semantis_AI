# Semantis Python SDK

Drop-in replacement for the OpenAI Python client with automatic semantic caching.

## Installation

```bash
pip install semantis
```

For automatic OpenAI fallback when Semantis is unreachable:

```bash
pip install semantis[openai]
```

## Quick Start

```python
from semantis import SemantisCache

cache = SemantisCache(api_key="sc-myorg-xxxxxxxx")

# OpenAI-compatible interface
response = cache.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is machine learning?"}],
)
print(response.choices[0].message.content)
print(f"Cache: {response.meta.hit} | Similarity: {response.meta.similarity}")
```

## Zero-Code Integration (Proxy Mode)

Point your existing OpenAI client at Semantis:

```python
import openai

client = openai.OpenAI(
    base_url="https://api.semantis.ai/v1",
    api_key="sc-myorg-xxxxxxxx",
)

# Existing code works unchanged - caching is transparent
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is ML?"}],
)
```

## Self-Hosted

```python
cache = SemantisCache(
    api_key="sc-myorg-xxxxxxxx",
    base_url="http://localhost:8000",
)
```

## Features

- **OpenAI-compatible**: Drop-in replacement, same interface
- **Automatic retry**: Exponential backoff on 429/5xx errors
- **Fallback**: If Semantis is unreachable, falls back to direct OpenAI (with `[openai]` extra)
- **Cache metadata**: Every response includes `meta.hit`, `meta.similarity`, `meta.latency_ms`
- **Context manager**: Use with `with` for automatic cleanup
