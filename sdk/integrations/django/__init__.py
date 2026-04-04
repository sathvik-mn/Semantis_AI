"""
Django Integration for Semantys Cache

Provides Django middleware for automatic semantic caching.
"""

from .middleware import SemanticCacheMiddleware

__all__ = ["SemanticCacheMiddleware"]

