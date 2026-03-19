"""
LangChain LLM wrapper for Semantis Cache.

Requires: pip install semantis langchain
"""
from typing import Optional, List, Any, Dict

from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from pydantic import Field


class SemantisCacheLLM(LLM):
    """
    LangChain-compatible LLM with automatic Semantis semantic caching.

    Example::

        from semantis.integrations.langchain import SemantisCacheLLM

        llm = SemantisCacheLLM(api_key="sc-your-key")
        response = llm("What is AI?")
        print(response)
    """

    api_key: str = Field(..., description="Semantis AI API key")
    base_url: Optional[str] = Field(None, description="API base URL")
    model: str = Field("gpt-4o-mini", description="Model to use")
    temperature: float = Field(0.2, description="Sampling temperature")
    timeout: Optional[float] = Field(30.0, description="Request timeout")

    _cache: Any = None  # lazy-initialized SemantisCache instance

    @property
    def _llm_type(self) -> str:
        return "semantis_cache"

    def _get_cache(self):
        if self._cache is None:
            from semantis import SemantisCache
            self._cache = SemantisCache(
                api_key=self.api_key,
                base_url=self.base_url or "https://api.semantis.ai",
                timeout=self.timeout or 30.0,
            )
        return self._cache

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        cache = self._get_cache()
        resp = cache.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
        )
        return resp.choices[0].message.content

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "base_url": self.base_url,
        }
