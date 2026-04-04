"""
Semantys AI Python SDK

Drop-in replacement for OpenAI with automatic semantic caching.

Usage:
    from semantys import SemantysCache

    cache = SemantysCache(api_key="sc-myorg-xxxxxxxx")
    response = cache.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is ML?"}],
    )
    print(response.choices[0].message.content)
"""

from semantys.client import SemantysCache
from semantys.models import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkDelta,
    ChatCompletionChunkChoice,
    CacheMeta,
    Usage,
)

__version__ = "0.1.0"
__all__ = [
    "SemantysCache",
    "ChatCompletion",
    "ChatCompletionMessage",
    "ChatCompletionChoice",
    "ChatCompletionChunk",
    "ChatCompletionChunkDelta",
    "ChatCompletionChunkChoice",
    "CacheMeta",
    "Usage",
]
