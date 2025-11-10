"""
FastAPI Integration for Semantis Cache

Provides FastAPI middleware for automatic semantic caching.
"""

from .middleware import SemanticCacheMiddleware, add_semantic_cache_middleware

__all__ = ["SemanticCacheMiddleware", "add_semantic_cache_middleware"]

