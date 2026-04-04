# Django Middleware Integration

Django middleware for automatic semantic caching of OpenAI API calls.

## Installation

```bash
pip install semantys-cache django
```

## Usage

### settings.py

```python
# Add middleware
MIDDLEWARE = [
    'semantys_cache.integrations.django.SemanticCacheMiddleware',
    # ... other middleware
]

# Configuration
SEMANTYS_CACHE_API_KEY = 'sc-your-key'
SEMANTYS_CACHE_BASE_URL = 'https://api.semantys.ai'  # Optional
SEMANTYS_CACHE_PATHS = ['/v1/chat/completions']  # Optional
```

### Environment Variables

```bash
export SEMANTYS_API_KEY="sc-your-key"
export SEMANTYS_API_URL="https://api.semantys.ai"
```

## How It Works

1. Middleware intercepts requests to configured paths
2. Extracts prompt from request body
3. Checks cache for matching or similar queries
4. Returns cached response if found (fast!)
5. Otherwise, passes request to original view

## Features

- ✅ Automatic caching of OpenAI API calls
- ✅ No code changes needed
- ✅ Transparent to your application
- ✅ Fast responses for cached queries
- ✅ Cost savings

