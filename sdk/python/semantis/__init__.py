"""
Semantis AI Python SDK

Drop-in replacement for OpenAI with automatic semantic caching.

Usage:
    from semantis import SemantisCache

    cache = SemantisCache(api_key="sc-myorg-xxxxxxxx")
    response = cache.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is ML?"}],
    )
    print(response.choices[0].message.content)
"""

from semantis.client import SemantisCache
from semantis.models import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionChoice,
    Usage,
)

__version__ = "0.1.0"
__all__ = [
    "SemantisCache",
    "ChatCompletion",
    "ChatCompletionMessage",
    "ChatCompletionChoice",
    "Usage",
]
