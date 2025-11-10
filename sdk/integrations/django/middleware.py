"""
Django Middleware for Semantis Cache

Automatically caches OpenAI API calls in Django applications.
"""
import os
import json
from typing import Optional, Callable
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin


class SemanticCacheMiddleware(MiddlewareMixin):
    """
    Django middleware for automatic semantic caching.
    
    Intercepts OpenAI API calls and caches them automatically.
    
    Example:
        >>> # In settings.py
        >>> MIDDLEWARE = [
        ...     'semantis_cache.integrations.django.SemanticCacheMiddleware',
        ...     # ... other middleware
        ... ]
        >>> 
        >>> # In settings.py
        >>> SEMANTIS_CACHE_API_KEY = 'sc-your-key'
        >>> SEMANTIS_CACHE_BASE_URL = 'https://api.semantis.ai'
        >>> SEMANTIS_CACHE_PATHS = ['/v1/chat/completions']
    """
    
    def __init__(self, get_response: Callable):
        """Initialize middleware."""
        super().__init__(get_response)
        self.get_response = get_response
        
        # Get configuration from settings
        from django.conf import settings
        self.api_key = getattr(settings, 'SEMANTIS_CACHE_API_KEY', None) or os.getenv('SEMANTIS_API_KEY')
        self.base_url = getattr(settings, 'SEMANTIS_CACHE_BASE_URL', None) or os.getenv('SEMANTIS_API_URL', 'https://api.semantis.ai')
        self.cache_paths = getattr(settings, 'SEMANTIS_CACHE_PATHS', ['/v1/chat/completions'])
        
        if not self.api_key:
            raise ValueError("API key is required. Set SEMANTIS_CACHE_API_KEY in settings or SEMANTIS_API_KEY environment variable.")
        
        # Initialize cache client
        try:
            from semantis_cache import SemanticCache
            self.cache = SemanticCache(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError(
                "semantis_cache package is required. Install it with: pip install semantis-cache"
            )
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process request and check cache."""
        # Check if this path should be cached
        if request.path not in self.cache_paths:
            return None
        
        # Only cache POST requests (OpenAI API calls)
        if request.method != 'POST':
            return None
        
        try:
            # Get request body
            body = json.loads(request.body)
            
            # Extract prompt from messages
            messages = body.get('messages', [])
            if not messages:
                return None
            
            # Get the last user message
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            if not user_messages:
                return None
            
            prompt = user_messages[-1].get('content', '')
            if not prompt:
                return None
            
            # Check cache
            try:
                response = self.cache.query(prompt, model=body.get('model', 'gpt-4o-mini'))
                
                # If cache hit, return cached response
                if response.cache_hit in ['exact', 'semantic']:
                    # Format as OpenAI response
                    import time
                    cached_response = {
                        'id': f'chatcmpl-cached-{hash(prompt)}',
                        'object': 'chat.completion',
                        'created': int(time.time()),
                        'model': body.get('model', 'gpt-4o-mini'),
                        'choices': [{
                            'index': 0,
                            'message': {
                                'role': 'assistant',
                                'content': response.answer
                            },
                            'finish_reason': 'stop'
                        }],
                        'usage': {
                            'prompt_tokens': 0,
                            'completion_tokens': 0,
                            'total_tokens': 0
                        },
                        'meta': {
                            'hit': response.cache_hit,
                            'similarity': response.similarity,
                            'latency_ms': response.latency_ms
                        }
                    }
                    
                    return JsonResponse(cached_response)
            
            except Exception as e:
                # If cache fails, continue to original view
                pass
        
        except Exception as e:
            # If anything fails, continue to original view
            pass
        
        # If no cache hit, continue to original view
        return None

