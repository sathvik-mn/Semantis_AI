"""
Semantys AI Client - OpenAI-compatible interface with automatic semantic caching.
"""

import json
import time
from typing import Generator, Iterator, Optional, List, Dict, Any, Union

import httpx

from semantys.models import ChatCompletion, ChatCompletionChunk


_DEFAULT_BASE_URL = "https://api.semantys.ai"
_DEFAULT_TIMEOUT = 60.0
_MAX_RETRIES = 3


class _Completions:
    """Mirrors openai.chat.completions interface."""

    def __init__(self, client: "SemantysCache"):
        self._client = client

    def create(
        self,
        *,
        model: str = "gpt-4o-mini",
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        stream: bool = False,
        ttl_seconds: int = 604800,
        **kwargs,
    ) -> Union[ChatCompletion, Iterator["ChatCompletionChunk"]]:
        """Create a chat completion (with automatic semantic caching).

        Accepts the same parameters as ``openai.chat.completions.create``.
        When ``stream=True``, returns an iterator of ``ChatCompletionChunk``.
        """
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
            "ttl_seconds": ttl_seconds,
        }
        payload.update(kwargs)

        if stream:
            return self._client._post_stream("/v1/chat/completions", json=payload)

        data = self._client._post("/v1/chat/completions", json=payload)
        return ChatCompletion.from_dict(data)


class _Chat:
    """Mirrors openai.chat namespace."""

    def __init__(self, client: "SemantysCache"):
        self.completions = _Completions(client)


class SemantysCache:
    """Semantys AI SDK client.

    Drop-in replacement for ``openai.OpenAI`` that routes requests through
    the Semantys semantic cache.

    Example::

        from semantys import SemantysCache

        cache = SemantysCache(api_key="sc-myorg-xxxxxxxx")
        resp = cache.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "What is ML?"}],
        )
        print(resp.choices[0].message.content)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _MAX_RETRIES,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "semantys-python/0.1.0",
            },
        )
        self.chat = _Chat(self)

    def _post(self, path: str, **kwargs) -> dict:
        """POST with retry + exponential backoff."""
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                resp = self._http.post(path, **kwargs)
                if resp.status_code == 429:
                    wait = min(2 ** attempt, 8)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    last_exc = e
                    time.sleep(min(2 ** attempt, 8))
                    continue
                raise
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                last_exc = e
                if attempt == self.max_retries - 1:
                    return self._openai_fallback(path, kwargs)
                time.sleep(min(2 ** attempt, 8))
        if last_exc:
            raise last_exc
        raise RuntimeError("Request failed after retries")

    def _post_stream(self, path: str, **kwargs) -> Generator[ChatCompletionChunk, None, None]:
        """POST with SSE streaming. Yields ChatCompletionChunk objects."""
        with self._http.stream("POST", path, **kwargs) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    return
                try:
                    data = json.loads(data_str)
                    yield ChatCompletionChunk.from_dict(data)
                except json.JSONDecodeError:
                    continue

    def _openai_fallback(self, path: str, kwargs: dict) -> dict:
        """When Semantys is unreachable, fall back to direct OpenAI call."""
        try:
            import openai as _openai
            payload = kwargs.get("json", {})
            # Remove Semantys-specific params that OpenAI doesn't accept
            openai_payload = {k: v for k, v in payload.items() if k not in ("ttl_seconds",)}
            client = _openai.OpenAI()
            resp = client.chat.completions.create(**openai_payload)
            return {
                "id": resp.id,
                "object": resp.object,
                "created": resp.created,
                "model": resp.model,
                "choices": [
                    {
                        "index": c.index,
                        "message": {"role": c.message.role, "content": c.message.content},
                        "finish_reason": c.finish_reason,
                    }
                    for c in resp.choices
                ],
                "usage": {
                    "prompt_tokens": resp.usage.prompt_tokens if resp.usage else None,
                    "completion_tokens": resp.usage.completion_tokens if resp.usage else None,
                    "total_tokens": resp.usage.total_tokens if resp.usage else None,
                },
                "meta": {"hit": "fallback", "similarity": 0.0, "latency_ms": 0, "strategy": "openai_fallback"},
            }
        except ImportError:
            raise RuntimeError(
                "Semantys API unreachable and openai package not installed for fallback. "
                "Install with: pip install semantys[openai]"
            )
        except Exception as e:
            raise RuntimeError(f"Both Semantys and OpenAI fallback failed: {e}")

    # ── Convenience methods ──

    def query(self, prompt: str, model: str = "gpt-4o-mini") -> dict:
        """Simple query interface (non-OpenAI-compatible)."""
        resp = self._http.get("/query", params={"prompt": prompt, "model": model})
        resp.raise_for_status()
        return resp.json()

    def health(self) -> dict:
        """Check Semantys API health."""
        resp = self._http.get("/health")
        resp.raise_for_status()
        return resp.json()

    def metrics(self) -> dict:
        """Get cache metrics for the authenticated tenant."""
        resp = self._http.get("/metrics")
        resp.raise_for_status()
        return resp.json()

    def close(self):
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
