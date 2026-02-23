"""
Redis Cache Backend for Semantis AI

Provides L1 (process-local) + L2 (Redis) + L3 (PostgreSQL) tiered caching.
Redis stores exact-match cache entries and embedding vectors per org namespace.
Falls back gracefully to in-memory-only mode if Redis is unavailable.
"""
import os
import json
import time
import struct
import hashlib
import logging
import threading
from typing import Optional, Dict, Tuple, List
from collections import OrderedDict

import numpy as np

logger = logging.getLogger("semantis.redis_cache")

REDIS_URL = os.getenv("REDIS_URL", "")
_redis_client = None
_redis_lock = threading.Lock()
_redis_available = None


def _get_redis():
    """Lazy-init Redis client. Returns None if Redis is not configured or unreachable."""
    global _redis_client, _redis_available
    if _redis_available is False:
        return None
    with _redis_lock:
        if _redis_client is not None:
            return _redis_client
        if not REDIS_URL:
            _redis_available = False
            logger.info("Redis not configured (REDIS_URL empty), using in-memory only")
            return None
        try:
            import redis
            _redis_client = redis.Redis.from_url(
                REDIS_URL,
                decode_responses=False,
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True,
            )
            _redis_client.ping()
            _redis_available = True
            logger.info("Redis connected: %s", REDIS_URL.split("@")[-1] if "@" in REDIS_URL else REDIS_URL)
            return _redis_client
        except Exception as e:
            _redis_available = False
            logger.warning("Redis unavailable (%s), falling back to in-memory", e)
            return None


# ── Key naming ──

def _exact_key(org_id: str, prompt_hash: str) -> str:
    return f"org:{org_id}:exact:{prompt_hash}"

def _emb_key(org_id: str, prompt_hash: str) -> str:
    return f"org:{org_id}:emb:{prompt_hash}"

def _meta_key(org_id: str) -> str:
    return f"org:{org_id}:meta"

def _settings_key(org_id: str) -> str:
    return f"org:{org_id}:settings"


# ── Embedding serialization (compact binary) ──

def _pack_embedding(emb: np.ndarray) -> bytes:
    """Pack float32 ndarray to bytes (4 bytes per float)."""
    return emb.astype(np.float32).tobytes()

def _unpack_embedding(data: bytes, dim: int = 3072) -> np.ndarray:
    """Unpack bytes back to float32 ndarray."""
    return np.frombuffer(data, dtype=np.float32).copy()


# ── Public API ──

def store_exact_match(org_id: str, prompt_hash: str, response: str, model: str, ttl_seconds: int = 604800):
    """Store an exact-match cache entry in Redis. TTL defaults to 7 days."""
    r = _get_redis()
    if r is None:
        return False
    try:
        key = _exact_key(org_id, prompt_hash)
        value = json.dumps({
            "response": response,
            "model": model,
            "created_at": time.time(),
            "use_count": 0,
        })
        r.setex(key, ttl_seconds, value.encode("utf-8"))
        return True
    except Exception as e:
        logger.warning("Redis store_exact_match failed: %s", e)
        return False


def get_exact_match(org_id: str, prompt_hash: str, model: str) -> Optional[str]:
    """Retrieve an exact-match cache entry from Redis."""
    r = _get_redis()
    if r is None:
        return None
    try:
        key = _exact_key(org_id, prompt_hash)
        data = r.get(key)
        if data is None:
            return None
        entry = json.loads(data.decode("utf-8"))
        if entry.get("model") != model:
            return None
        # Bump use_count async
        entry["use_count"] = entry.get("use_count", 0) + 1
        try:
            r.set(key, json.dumps(entry).encode("utf-8"), keepttl=True)
        except Exception:
            pass
        return entry["response"]
    except Exception as e:
        logger.warning("Redis get_exact_match failed: %s", e)
        return None


def store_embedding(org_id: str, prompt_hash: str, embedding: np.ndarray, ttl_seconds: int = 604800):
    """Store an embedding vector in Redis."""
    r = _get_redis()
    if r is None:
        return False
    try:
        key = _emb_key(org_id, prompt_hash)
        r.setex(key, ttl_seconds, _pack_embedding(embedding))
        return True
    except Exception as e:
        logger.warning("Redis store_embedding failed: %s", e)
        return False


def get_embedding(org_id: str, prompt_hash: str) -> Optional[np.ndarray]:
    """Retrieve an embedding vector from Redis."""
    r = _get_redis()
    if r is None:
        return None
    try:
        key = _emb_key(org_id, prompt_hash)
        data = r.get(key)
        if data is None:
            return None
        return _unpack_embedding(data)
    except Exception as e:
        logger.warning("Redis get_embedding failed: %s", e)
        return None


def store_org_settings(org_id: str, settings: dict):
    """Store org-level settings in Redis for fast access."""
    r = _get_redis()
    if r is None:
        return False
    try:
        key = _settings_key(org_id)
        r.set(key, json.dumps(settings).encode("utf-8"))
        return True
    except Exception as e:
        logger.warning("Redis store_org_settings failed: %s", e)
        return False


def get_org_settings(org_id: str) -> Optional[dict]:
    """Retrieve org-level settings from Redis."""
    r = _get_redis()
    if r is None:
        return None
    try:
        key = _settings_key(org_id)
        data = r.get(key)
        if data is None:
            return None
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        logger.warning("Redis get_org_settings failed: %s", e)
        return None


def increment_org_counter(org_id: str, field: str, amount: int = 1) -> int:
    """Increment an org-level counter (e.g., request_count, hits, misses)."""
    r = _get_redis()
    if r is None:
        return 0
    try:
        key = f"org:{org_id}:counters"
        return r.hincrby(key, field, amount)
    except Exception as e:
        logger.warning("Redis increment_org_counter failed: %s", e)
        return 0


def get_org_counters(org_id: str) -> dict:
    """Get all org counters."""
    r = _get_redis()
    if r is None:
        return {}
    try:
        key = f"org:{org_id}:counters"
        data = r.hgetall(key)
        return {k.decode(): int(v) for k, v in data.items()} if data else {}
    except Exception as e:
        logger.warning("Redis get_org_counters failed: %s", e)
        return {}


def flush_org(org_id: str) -> int:
    """Delete all Redis keys for an org (for testing or data deletion)."""
    r = _get_redis()
    if r is None:
        return 0
    try:
        pattern = f"org:{org_id}:*"
        keys = list(r.scan_iter(match=pattern, count=1000))
        if keys:
            return r.delete(*keys)
        return 0
    except Exception as e:
        logger.warning("Redis flush_org failed: %s", e)
        return 0


def is_available() -> bool:
    """Check if Redis is available."""
    return _get_redis() is not None


def health_check() -> dict:
    """Return Redis health info."""
    r = _get_redis()
    if r is None:
        return {"status": "unavailable", "mode": "in-memory"}
    try:
        info = r.info(section="memory")
        return {
            "status": "connected",
            "mode": "redis",
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "connected_clients": r.info(section="clients").get("connected_clients", 0),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
