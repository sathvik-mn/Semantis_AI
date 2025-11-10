"""
Base client for Semantis AI API
"""
import httpx
from typing import Optional, Dict, Any


class BaseClient:
    """Base HTTP client for Semantis AI API"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
    
    def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request"""
        response = self._client.request(method=method, url=path, json=json)
        response.raise_for_status()
        return response.json()
    
    def close(self):
        """Close HTTP client"""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

