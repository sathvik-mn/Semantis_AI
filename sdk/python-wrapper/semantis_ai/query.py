"""
Simple Query API - Simple interface for semantic caching
"""
import sys
from pathlib import Path
from typing import Optional, Union, Dict, Any

# Import OpenAPI client types
_parent_dir = Path(__file__).parent.parent.parent
_openapi_client_path = _parent_dir / "python" / "src"
if _openapi_client_path.exists():
    sys.path.insert(0, str(_openapi_client_path))

try:
    from semantis_ai_semantic_cache_api_client.api.default import simple_query_query_get
except ImportError:
    try:
        from semantis_ai_semantic_cache_api_client.api.default import simple_query_query_get
    except ImportError:
        simple_query_query_get = None


class SimpleQuery:
    """Simple query interface for semantic caching"""
    
    def __init__(self, openapi_client):
        """Initialize with OpenAPI client"""
        self._openapi_client = openapi_client
    
    def query(self, prompt: str, model: str = "gpt-4o-mini") -> "QueryResponse":
        """
        Simple query method - returns cached or fresh response.
        
        Caching is completely transparent - customers don't need to think about it.
        The service automatically:
        - Checks for exact matches (instant response)
        - Checks for semantic matches (fast response)
        - Falls back to LLM if no match (normal response)
        
        Args:
            prompt: Query string (e.g., "What is our refund policy?")
            model: Model to use (default: "gpt-4o-mini")
        
        Returns:
            QueryResponse with answer and cache metadata
        
        Example:
            >>> response = cache.query("What is AI?")
            >>> print(response.answer)
            >>> print(f"Cache hit: {response.cache_hit}")
        """
        if simple_query_query_get is None:
            raise ImportError("OpenAPI client not properly installed")
        
        # Make API request (caching happens automatically on server)
        response_data = simple_query_query_get.sync(
            client=self._openapi_client,
            prompt=prompt,
            model=model
        )
        
        # Return response object
        return QueryResponse(response_data)


class QueryResponse:
    """Query response with answer and cache metadata"""
    
    def __init__(self, data: Union[Dict[str, Any], Any]):
        """Initialize from OpenAPI response (dict or object)"""
        # Handle both dict and object responses
        if isinstance(data, dict):
            self._data = data
            self.answer = data.get("answer", "")
            self.meta = data.get("meta", {})
            self.metrics = data.get("metrics", {})
        else:
            # Object response from OpenAPI client
            self._data = data
            self.answer = getattr(data, "answer", "") or ""
            self.meta = getattr(data, "meta", {}) or {}
            self.metrics = getattr(data, "metrics", {}) or {}
    
    @property
    def cache_hit(self) -> str:
        """Get cache hit type: 'exact', 'semantic', or 'miss'"""
        if isinstance(self.meta, dict):
            return self.meta.get("hit", "miss")
        return getattr(self.meta, "hit", "miss")
    
    @property
    def similarity(self) -> float:
        """Get similarity score (for semantic hits)"""
        if isinstance(self.meta, dict):
            return self.meta.get("similarity", 0.0)
        return getattr(self.meta, "similarity", 0.0)
    
    @property
    def latency_ms(self) -> float:
        """Get response latency in milliseconds"""
        if isinstance(self.meta, dict):
            return self.meta.get("latency_ms", 0.0)
        return getattr(self.meta, "latency_ms", 0.0)
    
    def __repr__(self):
        return f"QueryResponse(answer={self.answer[:50]}..., cache_hit={self.cache_hit})"

