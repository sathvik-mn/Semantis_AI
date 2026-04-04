"""
LlamaIndex LLM wrapper for Semantys Cache
"""
from typing import Optional, Any, Dict
from llama_index.llms import CustomLLM
from llama_index.llms.types import CompletionResponse, CompletionResponseGen, LLMMetadata


class SemantysCacheLLM(CustomLLM):
    """
    LlamaIndex LLM wrapper for Semantys Cache.
    
    This provides a LlamaIndex-compatible LLM interface with automatic semantic caching.
    
    Example:
        >>> from semantys_cache.integrations.llamaindex import SemantysCacheLLM
        >>> 
        >>> llm = SemantysCacheLLM(api_key="sc-your-key")
        >>> 
        >>> # Use like any LlamaIndex LLM
        >>> response = llm.complete("What is AI?")
        >>> print(response.text)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        timeout: Optional[float] = 30.0,
        **kwargs: Any
    ):
        """Initialize Semantys Cache LLM."""
        super().__init__(**kwargs)
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
    
    @property
    def metadata(self) -> LLMMetadata:
        """Get LLM metadata."""
        return LLMMetadata(
            model_name=self.model,
            temperature=self.temperature,
        )
    
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Complete a prompt with caching."""
        try:
            from semantys import SemantysCache as SemanticCache
            
            # Initialize cache client
            cache = SemanticCache(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
            
            # Use simple query method
            response = cache.query(prompt, model=self.model)
            
            # Return completion response
            return CompletionResponse(text=response.answer)
            
        except ImportError:
            raise ImportError(
                "semantys_cache package is required. Install it with: pip install semantys-cache"
            )
        except Exception as e:
            raise Exception(f"Error calling Semantys Cache: {e}")
    
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        """Stream completion (not supported for caching)."""
        # For streaming, we'll just return the complete response
        response = self.complete(prompt, **kwargs)
        yield response

