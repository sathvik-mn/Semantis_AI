"""
OpenAI Proxy - Drop-in replacement for OpenAI ChatCompletion
"""
import os
from typing import Optional, List, Dict, Any
from .client import SemanticCache


class ChatCompletion:
    """
    Drop-in replacement for OpenAI ChatCompletion.
    
    Use this as a direct replacement for OpenAI's ChatCompletion class.
    All caching happens automatically and transparently.
    
    Example:
        >>> from semantis_ai.openai_proxy import ChatCompletion
        >>> 
        >>> # Same API as OpenAI
        >>> response = ChatCompletion.create(
        ...     model="gpt-4o-mini",
        ...     messages=[{"role": "user", "content": "What is AI?"}]
        ... )
        >>> 
        >>> print(response.choices[0].message.content)
        >>> print(f"Cache hit: {response.cache_hit}")  # Bonus: cache metadata!
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize ChatCompletion proxy.
        
        Args:
            api_key: Semantis AI API key (default: from SEMANTIS_API_KEY env var)
            base_url: API base URL (default: from SEMANTIS_API_URL env var or https://api.semantis.ai)
        """
        self._cache = SemanticCache(api_key=api_key, base_url=base_url)
    
    @staticmethod
    def create(
        model: str,
        messages: List[Dict[str, str]],
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Create a chat completion (drop-in replacement for OpenAI).
        
        This method has the same signature as OpenAI's ChatCompletion.create(),
        but uses semantic caching automatically.
        
        Args:
            model: Model to use (e.g., "gpt-4o-mini")
            messages: List of messages (e.g., [{"role": "user", "content": "Hello"}])
            api_key: Semantis AI API key (optional, uses env var if not provided)
            base_url: API base URL (optional)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            ChatCompletionResponse (OpenAI-compatible format with bonus cache metadata)
        
        Example:
            >>> # Before (OpenAI):
            >>> from openai import ChatCompletion
            >>> response = ChatCompletion.create(
            ...     model="gpt-4o-mini",
            ...     messages=[{"role": "user", "content": "What is AI?"}]
            ... )
            >>> 
            >>> # After (Semantis AI - drop-in replacement):
            >>> from semantis_ai.openai_proxy import ChatCompletion
            >>> response = ChatCompletion.create(
            ...     model="gpt-4o-mini",
            ...     messages=[{"role": "user", "content": "What is AI?"}]
            ... )
            >>> # Same API, automatic caching!
        """
        # Create cache client
        cache = SemanticCache(api_key=api_key, base_url=base_url)
        
        # Use chat completions (OpenAI-compatible)
        return cache.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )


# Alias for convenience
OpenAIProxy = ChatCompletion

