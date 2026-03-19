"""
Django Middleware for Semantis Cache

Automatically caches OpenAI API calls in Django applications.

Requires the main Semantis SDK: pip install semantis
"""
import json
import os
import time
from typing import Optional, Callable

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin


class SemanticCacheMiddleware(MiddlewareMixin):
    """
    Django middleware for automatic semantic caching.

    Add to MIDDLEWARE in settings.py::

        MIDDLEWARE = [
            'semantis.integrations.django.SemanticCacheMiddleware',
            ...
        ]

    Configuration (settings.py)::

        SEMANTIS_CACHE_API_KEY = 'sc-your-key'
        SEMANTIS_CACHE_BASE_URL = 'https://api.semantis.ai'  # optional
        SEMANTIS_CACHE_PATHS = ['/v1/chat/completions']        # optional
    """

    def __init__(self, get_response: Callable):
        super().__init__(get_response)
        self.get_response = get_response

        from django.conf import settings
        self.api_key = (
            getattr(settings, 'SEMANTIS_CACHE_API_KEY', None)
            or os.getenv('SEMANTIS_API_KEY')
        )
        self.base_url = (
            getattr(settings, 'SEMANTIS_CACHE_BASE_URL', None)
            or os.getenv('SEMANTIS_API_URL', 'https://api.semantis.ai')
        )
        self.cache_paths = getattr(
            settings, 'SEMANTIS_CACHE_PATHS', ['/v1/chat/completions']
        )

        if not self.api_key:
            raise ValueError(
                "API key required. Set SEMANTIS_CACHE_API_KEY in settings "
                "or SEMANTIS_API_KEY env var."
            )

        try:
            from semantis import SemantisCache
            self._cache = SemantisCache(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError(
                "semantis package is required. Install with: pip install semantis"
            )

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        if request.path not in self.cache_paths or request.method != 'POST':
            return None

        try:
            body = json.loads(request.body)
            messages = body.get('messages', [])
            user_messages = [m for m in messages if m.get('role') == 'user']
            if not user_messages:
                return None

            prompt = user_messages[-1].get('content', '')
            if not prompt:
                return None

            resp = self._cache.chat.completions.create(
                model=body.get('model', 'gpt-4o-mini'),
                messages=messages,
                temperature=body.get('temperature', 0.2),
            )
            if resp.meta and resp.meta.hit in ('exact', 'semantic'):
                return JsonResponse({
                    'id': resp.id,
                    'object': resp.object,
                    'created': resp.created,
                    'model': resp.model,
                    'choices': [
                        {
                            'index': c.index,
                            'message': {'role': c.message.role, 'content': c.message.content},
                            'finish_reason': c.finish_reason,
                        }
                        for c in resp.choices
                    ],
                    'usage': {
                        'prompt_tokens': resp.usage.prompt_tokens if resp.usage else 0,
                        'completion_tokens': resp.usage.completion_tokens if resp.usage else 0,
                        'total_tokens': resp.usage.total_tokens if resp.usage else 0,
                    },
                    'meta': {
                        'hit': resp.meta.hit,
                        'similarity': resp.meta.similarity,
                        'latency_ms': resp.meta.latency_ms,
                    },
                })
        except Exception:
            pass

        return None
