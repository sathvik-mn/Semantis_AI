"""
Django Middleware for Semantys Cache

Automatically caches OpenAI API calls in Django applications.

Requires the main Semantys SDK: pip install semantys
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
            'semantys.integrations.django.SemanticCacheMiddleware',
            ...
        ]

    Configuration (settings.py)::

        SEMANTYS_CACHE_API_KEY = 'sc-your-key'
        SEMANTYS_CACHE_BASE_URL = 'https://api.semantys.ai'  # optional
        SEMANTYS_CACHE_PATHS = ['/v1/chat/completions']        # optional
    """

    def __init__(self, get_response: Callable):
        super().__init__(get_response)
        self.get_response = get_response

        from django.conf import settings
        self.api_key = (
            getattr(settings, 'SEMANTYS_CACHE_API_KEY', None)
            or os.getenv('SEMANTYS_API_KEY')
        )
        self.base_url = (
            getattr(settings, 'SEMANTYS_CACHE_BASE_URL', None)
            or os.getenv('SEMANTYS_API_URL', 'https://api.semantys.ai')
        )
        self.cache_paths = getattr(
            settings, 'SEMANTYS_CACHE_PATHS', ['/v1/chat/completions']
        )

        if not self.api_key:
            raise ValueError(
                "API key required. Set SEMANTYS_CACHE_API_KEY in settings "
                "or SEMANTYS_API_KEY env var."
            )

        try:
            from semantys import SemantysCache
            self._cache = SemantysCache(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError(
                "semantys package is required. Install with: pip install semantys"
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
