"""
FastAPI Middleware for Semantis Cache

Automatically caches OpenAI API calls in FastAPI applications.
"""
from typing import Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import json
import os


class SemanticCacheMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic semantic caching.
    
    Intercepts OpenAI API calls and caches them automatically.
    
    Example:
        >>> from fastapi import FastAPI
        >>> from semantis_cache.integrations.fastapi import SemanticCacheMiddleware
        >>> 
        >>> app = FastAPI()
        >>> 
        >>> # Add middleware
        >>> app.add_middleware(
        ...     SemanticCacheMiddleware,
        ...     api_key="sc-your-key",
        ...     cache_paths=["/v1/chat/completions"]  # Paths to cache
        ... )
    """
    
    def __init__(
        self,
        app,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        cache_paths: Optional[list] = None,
    ):
        """
        Initialize semantic cache middleware.
        
        Args:
            app: FastAPI application
            api_key: Semantis AI API key (default: from SEMANTIS_API_KEY env var)
            base_url: API base URL (default: from SEMANTIS_API_URL env var)
            cache_paths: List of paths to cache (default: ["/v1/chat/completions"])
        """
        super().__init__(app)
        self.api_key = api_key or os.getenv("SEMANTIS_API_KEY")
        self.base_url = base_url or os.getenv("SEMANTIS_API_URL", "https://api.semantis.ai")
        self.cache_paths = cache_paths or ["/v1/chat/completions"]
        
        if not self.api_key:
            raise ValueError("API key is required. Provide it as argument or set SEMANTIS_API_KEY environment variable.")
        
        # Initialize cache client
        try:
            from semantis_cache import SemanticCache
            self.cache = SemanticCache(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError(
                "semantis_cache package is required. Install it with: pip install semantis-cache"
            )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Intercept requests and cache responses."""
        # Check if this path should be cached
        if request.url.path not in self.cache_paths:
            return await call_next(request)
        
        # Only cache POST requests (OpenAI API calls)
        if request.method != "POST":
            return await call_next(request)
        
        try:
            # Get request body
            body = await request.json()
            
            # Extract prompt from messages
            messages = body.get("messages", [])
            if not messages:
                return await call_next(request)
            
            # Get the last user message
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if not user_messages:
                return await call_next(request)
            
            prompt = user_messages[-1].get("content", "")
            if not prompt:
                return await call_next(request)
            
            # Check cache
            try:
                response = self.cache.query(prompt, model=body.get("model", "gpt-4o-mini"))
                
                # If cache hit, return cached response
                if response.cache_hit in ["exact", "semantic"]:
                    # Format as OpenAI response
                    cached_response = {
                        "id": f"chatcmpl-cached-{hash(prompt)}",
                        "object": "chat.completion",
                        "created": int(__import__("time").time()),
                        "model": body.get("model", "gpt-4o-mini"),
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response.answer
                            },
                            "finish_reason": "stop"
                        }],
                        "usage": {
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0
                        },
                        "meta": {
                            "hit": response.cache_hit,
                            "similarity": response.similarity,
                            "latency_ms": response.latency_ms
                        }
                    }
                    
                    return JSONResponse(content=cached_response)
            
            except Exception as e:
                # If cache fails, continue to original endpoint
                pass
        
        except Exception as e:
            # If anything fails, continue to original endpoint
            pass
        
        # If no cache hit, continue to original endpoint
        return await call_next(request)


def add_semantic_cache_middleware(
    app,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    cache_paths: Optional[list] = None,
):
    """
    Convenience function to add semantic cache middleware to FastAPI app.
    
    Example:
        >>> from fastapi import FastAPI
        >>> from semantis_cache.integrations.fastapi import add_semantic_cache_middleware
        >>> 
        >>> app = FastAPI()
        >>> add_semantic_cache_middleware(app, api_key="sc-your-key")
    """
    app.add_middleware(
        SemanticCacheMiddleware,
        api_key=api_key,
        base_url=base_url,
        cache_paths=cache_paths,
    )

