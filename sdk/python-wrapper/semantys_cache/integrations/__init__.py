"""
Integrations for Semantys Cache

Provides integrations for LangChain, LlamaIndex, FastAPI, and more.
"""

# Import integrations
try:
    from ..integrations.langchain import SemantysCacheLLM as LangChainLLM
    __all__ = ["LangChainLLM"]
except ImportError:
    __all__ = []

# Note: Other integrations are in separate packages
# - LangChain: semantys_cache.integrations.langchain
# - LlamaIndex: semantys_cache.integrations.llamaindex
# - FastAPI: semantys_cache.integrations.fastapi
# - Django: semantys_cache.integrations.django
# - RAG: semantys_cache.integrations.rag
# - SQL: semantys_cache.integrations.sql

