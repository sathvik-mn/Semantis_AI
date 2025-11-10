"""
RAG-optimized caching for Semantis Cache

Provides specialized caching for RAG applications that combine context and questions.
"""
from typing import List, Optional, Dict, Any
from semantis_cache import SemanticCache


class SemantisRAG:
    """
    RAG-optimized caching for semantic cache.
    
    This class provides specialized caching for RAG applications where
    queries combine context (retrieved documents) with questions.
    
    Example:
        >>> from semantis_cache.integrations.rag import SemantisRAG
        >>> 
        >>> rag = SemantisRAG(api_key="sc-your-key")
        >>> 
        >>> # Cache RAG queries with context
        >>> context = ["Document 1 content...", "Document 2 content..."]
        >>> response = rag.query(
        ...     question="What is the main topic?",
        ...     context=context
        ... )
        >>> print(response.answer)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        cache_context: bool = True,
    ):
        """
        Initialize RAG cache.
        
        Args:
            api_key: Semantis AI API key
            base_url: API base URL (optional)
            model: Model to use (default: "gpt-4o-mini")
            cache_context: Whether to include context in cache key (default: True)
        """
        self.cache = SemanticCache(api_key=api_key, base_url=base_url)
        self.model = model
        self.cache_context = cache_context
    
    def query(
        self,
        question: str,
        context: List[str],
        **kwargs
    ) -> Any:
        """
        Query with context (RAG pattern).
        
        This method combines context and question into a prompt and caches it.
        The cache key includes both context and question for better matching.
        
        Args:
            question: User question
            context: List of context documents
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            QueryResponse with answer and cache metadata
        
        Example:
            >>> response = rag.query(
            ...     question="What is the main topic?",
            ...     context=["Document 1...", "Document 2..."]
            ... )
            >>> print(response.answer)
            >>> print(f"Cache hit: {response.cache_hit}")
        """
        # Combine context and question
        context_str = "\n\n".join(context) if isinstance(context, list) else str(context)
        
        if self.cache_context:
            # Include context in prompt for caching
            prompt = f"Context:\n{context_str}\n\nQuestion: {question}"
        else:
            # Only cache the question (context may vary)
            prompt = question
        
        # Query cache
        response = self.cache.query(prompt, model=self.model)
        
        return response
    
    def query_with_metadata(
        self,
        question: str,
        context: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Query with context and metadata.
        
        This method allows you to include metadata (e.g., document IDs, sources)
        that can be used for cache key generation or response filtering.
        
        Args:
            question: User question
            context: List of context documents
            metadata: Optional metadata (e.g., {"sources": ["doc1", "doc2"]})
            **kwargs: Additional parameters
        
        Returns:
            QueryResponse with answer and cache metadata
        """
        # Combine context and question
        context_str = "\n\n".join(context) if isinstance(context, list) else str(context)
        
        # Include metadata in prompt if provided
        if metadata:
            metadata_str = "\n".join([f"{k}: {v}" for k, v in metadata.items()])
            prompt = f"Metadata:\n{metadata_str}\n\nContext:\n{context_str}\n\nQuestion: {question}"
        else:
            prompt = f"Context:\n{context_str}\n\nQuestion: {question}"
        
        # Query cache
        response = self.cache.query(prompt, model=self.model)
        
        return response

