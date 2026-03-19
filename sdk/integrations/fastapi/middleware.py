"""
FastAPI Middleware for Semantis Cache

Automatically caches OpenAI API calls in FastAPI applications.

Requires the main Semantis SDK: pip install semantis
"""
from typing import Optional, Callable, List
import time
import os

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class SemanticCacheMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic semantic caching.

    Intercepts POST requests to specified paths (e.g. /v1/chat/completions)
    and serves cached responses when a semantic match is found.

    Example::

        from fastapi import FastAPI
        from semantis.integrations.fastapi import SemanticCacheMiddleware

        app = FastAPI()
        app.add_middleware(
            SemanticCacheMiddleware,
            api_key="sc-your-key",
            base_url="https://api.semantis.ai",
        )
    """

    def __init__(
        self,
        app,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        cache_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.api_key = api_key or os.getenv("SEMANTIS_API_KEY")
        self.base_url = base_url or os.getenv("SEMANTIS_API_URL", "https://api.semantis.ai")
        self.cache_paths = cache_paths or ["/v1/chat/completions"]

        if not self.api_key:
            raise ValueError(
                "API key is required. Provide it as argument or set SEMANTIS_API_KEY."
            )

        try:
            from semantis import SemantisCache
            self._cache = SemantisCache(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError(
                "semantis package is required. Install with: pip install semantis"
            )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path not in self.cache_paths or request.method != "POST":
            return await call_next(request)

        try:
            body = await request.json()
            messages = body.get("messages", [])
            user_messages = [m for m in messages if m.get("role") == "user"]
            if not user_messages:
                return await call_next(request)

            prompt = user_messages[-1].get("content", "")
            if not prompt:
                return await call_next(request)

            # Try to serve from cache via the chat completions endpoint
            resp = self._cache.chat.completions.create(
                model=body.get("model", "gpt-4o-mini"),
                messages=messages,
                temperature=body.get("temperature", 0.2),
            )
            # Only short-circuit if we got a cache hit
            if resp.meta and resp.meta.hit in ("exact", "semantic"):
                return JSONResponse(content={
                    "id": resp.id,
                    "object": resp.object,
                    "created": resp.created,
                    "model": resp.model,
                    "choices": [
                        {
                            "index": c.index,
                            "message": {"role": c.message.role, "content": c.message.content},
                            "finish_reason": c.finish_reason,
                        }
                        for c in resp.choices
                    ],
                    "usage": {
                        "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                        "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
                        "total_tokens": resp.usage.total_tokens if resp.usage else 0,
                    },
                    "meta": {
                        "hit": resp.meta.hit,
                        "similarity": resp.meta.similarity,
                        "latency_ms": resp.meta.latency_ms,
                    },
                })
        except Exception:
            # On any failure, fall through to the real endpoint
            pass

        return await call_next(request)
