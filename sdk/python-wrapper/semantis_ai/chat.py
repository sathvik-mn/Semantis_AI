"""
Chat Completions API - OpenAI-compatible interface
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Import OpenAPI client types
_parent_dir = Path(__file__).parent.parent.parent
_openapi_client_path = _parent_dir / "python" / "src"
if _openapi_client_path.exists():
    sys.path.insert(0, str(_openapi_client_path))

try:
    from semantis_ai_semantic_cache_api_client.api.default import (
        openai_compatible_v1_chat_completions_post
    )
    from semantis_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage
except ImportError:
    try:
        from semantis_ai_semantic_cache_api_client.api.default import (
            openai_compatible_v1_chat_completions_post
        )
        from semantis_ai_semantic_cache_api_client.models import ChatRequest, ChatMessage
    except ImportError:
        openai_compatible_v1_chat_completions_post = None
        ChatRequest = None
        ChatMessage = None


class ChatCompletions:
    """Chat completions with automatic semantic caching"""
    
    def __init__(self, openapi_client):
        """Initialize with OpenAPI client"""
        self._openapi_client = openapi_client
    
    def create(
        self,
        model: str,
        messages: Union[List[Dict[str, str]], List[ChatMessage]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> "ChatCompletionResponse":
        """
        Create a chat completion with automatic semantic caching.
        
        Caching is completely transparent - customers don't need to think about it.
        The service automatically:
        - Checks for exact matches (instant response)
        - Checks for semantic matches (fast response)
        - Falls back to LLM if no match (normal response)
        
        Args:
            model: Model to use (e.g., "gpt-4o-mini")
            messages: List of messages (e.g., [{"role": "user", "content": "Hello"}])
            temperature: Sampling temperature (optional)
            max_tokens: Maximum tokens to generate (optional)
            **kwargs: Additional parameters (e.g., ttl_seconds)
        
        Returns:
            ChatCompletionResponse with cached or fresh response
        
        Example:
            >>> response = cache.chat.completions.create(
            ...     model="gpt-4o-mini",
            ...     messages=[{"role": "user", "content": "What is AI?"}]
            ... )
            >>> print(response.choices[0].message.content)
            >>> print(f"Cache hit: {response.cache_hit}")  # 'exact', 'semantic', or 'miss'
        """
        if openai_compatible_v1_chat_completions_post is None:
            raise ImportError("OpenAPI client not properly installed")
        
        # Convert messages to ChatMessage objects if needed
        if messages and isinstance(messages[0], dict):
            chat_messages = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in messages
            ]
        else:
            chat_messages = messages
        
        # Create chat request
        request = ChatRequest(
            model=model,
            messages=chat_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Make API request (caching happens automatically on server)
        response_data = openai_compatible_v1_chat_completions_post.sync(
            client=self._openapi_client,
            body=request
        )
        
        # Return response object
        return ChatCompletionResponse(response_data)


class ChatCompletionResponse:
    """Chat completion response (OpenAI-compatible format)"""
    
    def __init__(self, data: Union[Dict[str, Any], Any]):
        """Initialize from OpenAPI response (dict or object)"""
        # Handle both dict and object responses
        if isinstance(data, dict):
            self._data = data
            self.id = data.get("id")
            self.object = data.get("object", "chat.completion")
            self.created = data.get("created")
            self.model = data.get("model")
            self.choices = [Choice(c) for c in data.get("choices", [])]
            self.usage = data.get("usage")
            self.meta = data.get("meta", {})
        else:
            # Object response from OpenAPI client
            self._data = data
            self.id = getattr(data, "id", None)
            self.object = getattr(data, "object", "chat.completion")
            self.created = getattr(data, "created", None)
            self.model = getattr(data, "model", None)
            self.choices = [Choice(c) for c in (getattr(data, "choices", []) or [])]
            self.usage = getattr(data, "usage", None)
            self.meta = getattr(data, "meta", {}) or {}
    
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
        return f"ChatCompletionResponse(id={self.id}, cache_hit={self.cache_hit})"


class Choice:
    """Chat completion choice"""
    
    def __init__(self, data: Union[Dict[str, Any], Any]):
        """Initialize from dict or object"""
        if isinstance(data, dict):
            self._data = data
            self.index = data.get("index")
            self.message = Message(data.get("message", {}))
            self.finish_reason = data.get("finish_reason")
        else:
            self._data = data
            self.index = getattr(data, "index", None)
            self.message = Message(getattr(data, "message", None) or {})
            self.finish_reason = getattr(data, "finish_reason", None)


class Message:
    """Chat message"""
    
    def __init__(self, data: Union[Dict[str, Any], Any]):
        """Initialize from dict or object"""
        if isinstance(data, dict):
            self._data = data
            self.role = data.get("role")
            self.content = data.get("content", "")
        else:
            self._data = data
            self.role = getattr(data, "role", None)
            self.content = getattr(data, "content", "") or ""

