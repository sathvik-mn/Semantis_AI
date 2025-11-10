"""
Semantis AI Client - OpenAI-compatible interface with automatic caching
"""
import os
import sys
from pathlib import Path
from typing import Optional

# Add generated OpenAPI client to path
_parent_dir = Path(__file__).parent.parent.parent
_openapi_client_path = _parent_dir / "python" / "src"
if _openapi_client_path.exists():
    sys.path.insert(0, str(_openapi_client_path))

try:
    from semantis_ai_semantic_cache_api_client import Client as OpenAPIClient
    from semantis_ai_semantic_cache_api_client.api.default import (
        openai_compatible_v1_chat_completions_post
    )
    from semantis_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage
except ImportError:
    # Fallback: try to import from installed package
    try:
        from semantis_ai_semantic_cache_api_client import Client as OpenAPIClient
        from semantis_ai_semantic_cache_api_client.api.default import (
            openai_compatible_v1_chat_completions_post
        )
        from semantis_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage
    except ImportError:
        OpenAPIClient = None
        openai_compatible_v1_chat_completions_post = None
        ChatRequest = None
        ChatMessage = None

from .chat import ChatCompletions
from .query import SimpleQuery


class SemanticCache:
    """
    Semantis AI Semantic Cache Client
    
    Provides OpenAI-compatible interface with automatic semantic caching.
    Caching is transparent - customers don't need to think about it.
    
    Example - Simple Query:
        >>> from semantis_ai import SemanticCache
        >>> 
        >>> cache = SemanticCache(api_key="sc-your-key")
        >>> 
        >>> # Simple query method
        >>> response = cache.query("What is our refund policy?")
        >>> print(response.answer)
        >>> print(f"Cache hit: {response.cache_hit}")
    
    Example - OpenAI-Compatible:
        >>> response = cache.chat.completions.create(
        ...     model="gpt-4o-mini",
        ...     messages=[{"role": "user", "content": "What is AI?"}]
        ... )
        >>> 
        >>> print(response.choices[0].message.content)
        >>> print(f"Cache hit: {response.cache_hit}")  # 'exact', 'semantic', or 'miss'
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        """
        Initialize Semantis AI client.
        
        Args:
            api_key: Your Semantis AI API key (format: sc-{tenant}-{anything})
                    If not provided, will try to get from SEMANTIS_API_KEY env var
            base_url: API base URL (default: https://api.semantis.ai or http://localhost:8000 for dev)
            timeout: Request timeout in seconds (default: 30.0)
        """
        if OpenAPIClient is None:
            raise ImportError(
                "OpenAPI client not found. Please ensure the SDK is properly installed.\n"
                "Run: pip install -e sdk/python"
            )
        
        # Get API key from env if not provided
        if api_key is None:
            api_key = os.getenv("SEMANTIS_API_KEY")
            if api_key is None:
                raise ValueError(
                    "API key is required. Provide it as argument or set SEMANTIS_API_KEY environment variable."
                )
        
        # Set default base URL
        if base_url is None:
            base_url = os.getenv("SEMANTIS_API_URL", "http://localhost:8000")
        
        # Ensure API key has Bearer prefix
        if not api_key.startswith("Bearer "):
            api_key = f"Bearer {api_key}"
        
        # Initialize OpenAPI client
        self._openapi_client = OpenAPIClient(
            base_url=base_url,
            headers={"Authorization": api_key},
            timeout=timeout or 30.0,
        )
        
        # Store for access
        self._api_key = api_key
        self._base_url = base_url
        
        # Initialize chat completions
        self.chat = ChatCompletions(self._openapi_client)
        
        # Initialize simple query
        self._query_client = SimpleQuery(self._openapi_client)
    
    def query(self, prompt: str, model: str = "gpt-4o-mini"):
        """
        Simple query method - returns response with answer and cache metadata.
        
        This is the simplest way to use the semantic cache. Just provide a prompt
        and get a cached or fresh response.
        
        Args:
            prompt: Query string (e.g., "What is our refund policy?")
            model: Model to use (default: "gpt-4o-mini")
        
        Returns:
            QueryResponse with answer, cache_hit, similarity, latency_ms
        
        Example:
            >>> cache = SemanticCache(api_key="sc-your-key")
            >>> response = cache.query("What is AI?")
            >>> print(response.answer)
            >>> print(f"Cache hit: {response.cache_hit}")
            >>> print(f"Similarity: {response.similarity}")
            >>> print(f"Latency: {response.latency_ms}ms")
        """
        return self._query_client.query(prompt, model)
    
    @property
    def api_key(self) -> str:
        """Get API key"""
        return self._api_key
    
    @property
    def base_url(self) -> str:
        """Get base URL"""
        return self._base_url

