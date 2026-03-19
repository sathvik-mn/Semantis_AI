# ⚠️ DEPRECATED — Use `semantis` instead

This package (`semantis-cache` / `semantis_ai`) is **deprecated**. It wraps an auto-generated OpenAPI client that is fragile and hard to maintain.

**Use the main SDK instead:**

```bash
pip install semantis
```

```python
from semantis import SemantisCache

cache = SemantisCache(api_key="sc-your-key")

# Simple query
response = cache.query("What is our refund policy?")
print(response.answer)

# OpenAI-compatible
response = cache.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}],
)
print(response.choices[0].message.content)
```

The main SDK (`sdk/python/`) is a clean, httpx-based client with:
- OpenAI-compatible `chat.completions.create()` interface
- Retry with exponential backoff
- Automatic fallback to direct OpenAI when Semantis is unreachable
- No dependency on generated code

See [sdk/python/](../python/) for the production SDK.
