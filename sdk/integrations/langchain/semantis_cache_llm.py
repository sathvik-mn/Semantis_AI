"""
LangChain LLM wrapper for Semantis Cache
"""
from typing import Optional, List, Any, Dict
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from pydantic import Field


class SemantisCacheLLM(LLM):
    """
    LangChain LLM wrapper for Semantis Cache.
    
    This provides a LangChain-compatible LLM interface with automatic semantic caching.
    
    Example:
        >>> from semantis_cache.integrations.langchain import SemantisCacheLLM
        >>> 
        >>> llm = SemantisCacheLLM(api_key="sc-your-key")
        >>> 
        >>> # Use like any LangChain LLM
        >>> response = llm("What is AI?")
        >>> print(response)
    """
    
    api_key: str = Field(..., description="Semantis AI API key")
    base_url: Optional[str] = Field(None, description="API base URL")
    model: str = Field("gpt-4o-mini", description="Model to use")
    temperature: float = Field(0.2, description="Sampling temperature")
    timeout: Optional[float] = Field(30.0, description="Request timeout")
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "semantis_cache"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the LLM with caching."""
        try:
            from semantis_cache import SemanticCache
            
            # Initialize cache client
            cache = SemanticCache(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
            
            # Use simple query method
            response = cache.query(prompt, model=self.model)
            
            # Return answer
            return response.answer
            
        except ImportError:
            raise ImportError(
                "semantis_cache package is required. Install it with: pip install semantis-cache"
            )
        except Exception as e:
            raise Exception(f"Error calling Semantis Cache: {e}")
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "base_url": self.base_url,
        }

