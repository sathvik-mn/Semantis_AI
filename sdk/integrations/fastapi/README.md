# FastAPI Middleware Integration

FastAPI middleware for automatic semantic caching of OpenAI API calls.

## Installation

```bash
pip install semantis-cache fastapi
```

## Usage

### Option 1: Add Middleware Directly

```python
from fastapi import FastAPI
from semantis_cache.integrations.fastapi import SemanticCacheMiddleware

app = FastAPI()

# Add middleware
app.add_middleware(
    SemanticCacheMiddleware,
    api_key="sc-your-key",
    cache_paths=["/v1/chat/completions"]  # Paths to cache
)
```

### Option 2: Use Convenience Function

```python
from fastapi import FastAPI
from semantis_cache.integrations.fastapi import add_semantic_cache_middleware

app = FastAPI()

# Add middleware
add_semantic_cache_middleware(app, api_key="sc-your-key")
```

## How It Works

1. Middleware intercepts requests to `/v1/chat/completions`
2. Extracts prompt from request body
3. Checks cache for matching or similar queries
4. Returns cached response if found (fast!)
5. Otherwise, passes request to original endpoint

## Configuration

```python
app.add_middleware(
    SemanticCacheMiddleware,
    api_key="sc-your-key",
    base_url="https://api.semantis.ai",  # Optional
    cache_paths=["/v1/chat/completions", "/v1/completions"]  # Optional
)
```

## Environment Variables

```bash
export SEMANTIS_API_KEY="sc-your-key"
export SEMANTIS_API_URL="https://api.semantis.ai"
```

## Features

- ✅ Automatic caching of OpenAI API calls
- ✅ No code changes needed
- ✅ Transparent to your application
- ✅ Fast responses for cached queries
- ✅ Cost savings

