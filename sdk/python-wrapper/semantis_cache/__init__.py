"""
Semantis Cache - Semantic Caching SDK

Easy-to-use SDK for semantic caching in LLM applications.
Provides OpenAI-compatible interface with automatic caching.

Example - Simple Query:
    >>> from semantis_cache import SemanticCache
    >>> 
    >>> cache = SemanticCache(api_key="sc-your-key")
    >>> response = cache.query("What is our refund policy?")
    >>> print(response.answer)
    >>> print(f"Cache hit: {response.cache_hit}")

Example - OpenAI-Compatible:
    >>> response = cache.chat.completions.create(
    ...     model="gpt-4o-mini",
    ...     messages=[{"role": "user", "content": "What is AI?"}]
    ... )
    >>> print(response.choices[0].message.content)

Example - OpenAI Proxy (Drop-in Replacement):
    >>> from semantis_cache.openai_proxy import ChatCompletion
    >>> response = ChatCompletion.create(
    ...     model="gpt-4o-mini",
    ...     messages=[{"role": "user", "content": "What is AI?"}]
    ... )
"""

from .client import SemanticCache
from .openai_proxy import ChatCompletion

__version__ = "1.0.0"

__all__ = ["SemanticCache", "ChatCompletion", "__version__"]
