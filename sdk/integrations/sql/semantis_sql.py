"""
SQL/BI Caching Integration for Semantis Cache

Provides specialized caching for natural-language SQL queries and BI applications.
"""
from typing import Optional, Dict, Any
from semantis_cache import SemanticCache


class SemantisSQL:
    """
    SQL/BI-optimized caching for semantic cache.
    
    This class provides specialized caching for natural-language SQL queries
    and BI applications where similar questions should return cached SQL results.
    
    Example:
        >>> from semantis_cache.integrations.sql import SemantisSQL
        >>> 
        >>> sql_cache = SemantisSQL(api_key="sc-your-key")
        >>> 
        >>> # Cache SQL queries
        >>> response = sql_cache.query(
        ...     question="What are the top 10 customers by revenue?",
        ...     schema="customers, orders, products"
        ... )
        >>> print(response.answer)  # SQL query or result
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        cache_schema: bool = False,
    ):
        """
        Initialize SQL cache.
        
        Args:
            api_key: Semantis AI API key
            base_url: API base URL (optional)
            model: Model to use (default: "gpt-4o-mini")
            cache_schema: Whether to include schema in cache key (default: False)
        """
        self.cache = SemanticCache(api_key=api_key, base_url=base_url)
        self.model = model
        self.cache_schema = cache_schema
    
    def query(
        self,
        question: str,
        schema: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Query with SQL context.
        
        This method caches natural-language SQL queries. Similar questions
        will return cached SQL queries or results.
        
        Args:
            question: Natural language question (e.g., "What are the top 10 customers?")
            schema: Optional database schema description
            **kwargs: Additional parameters
        
        Returns:
            QueryResponse with SQL query/result and cache metadata
        
        Example:
            >>> response = sql_cache.query(
            ...     question="What are the top 10 customers by revenue?",
            ...     schema="customers(id, name, revenue), orders(customer_id, amount)"
            ... )
            >>> print(response.answer)  # SQL query or result
        """
        # Build prompt
        if schema and self.cache_schema:
            prompt = f"Schema:\n{schema}\n\nQuestion: {question}"
        else:
            prompt = question
        
        # Query cache
        response = self.cache.query(prompt, model=self.model)
        
        return response
    
    def query_with_result(
        self,
        question: str,
        sql_query: str,
        result: Any,
        schema: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Cache SQL query and result.
        
        This method allows you to cache both the SQL query and its result.
        Similar questions will return cached results.
        
        Args:
            question: Natural language question
            sql_query: Generated SQL query
            result: SQL query result
            schema: Optional database schema
            **kwargs: Additional parameters
        
        Returns:
            QueryResponse with cached result
        """
        # Build prompt with SQL and result
        if schema:
            prompt = f"Schema:\n{schema}\n\nQuestion: {question}\n\nSQL: {sql_query}\n\nResult: {result}"
        else:
            prompt = f"Question: {question}\n\nSQL: {sql_query}\n\nResult: {result}"
        
        # Query cache (this will cache the result)
        response = self.cache.query(prompt, model=self.model)
        
        return response

