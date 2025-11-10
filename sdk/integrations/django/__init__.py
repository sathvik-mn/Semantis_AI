"""
Django Integration for Semantis Cache

Provides Django middleware for automatic semantic caching.
"""

from .middleware import SemanticCacheMiddleware

__all__ = ["SemanticCacheMiddleware"]

