"""
Integrations for Semantis Cache

Provides integrations for LangChain, LlamaIndex, FastAPI, and more.
"""

# Import integrations
try:
    from ..integrations.langchain import SemantisCacheLLM as LangChainLLM
    __all__ = ["LangChainLLM"]
except ImportError:
    __all__ = []

# Note: Other integrations are in separate packages
# - LangChain: semantis_cache.integrations.langchain
# - LlamaIndex: semantis_cache.integrations.llamaindex
# - FastAPI: semantis_cache.integrations.fastapi
# - Django: semantis_cache.integrations.django
# - RAG: semantis_cache.integrations.rag
# - SQL: semantis_cache.integrations.sql

