"""
Authentication module - Supabase JWT verification.

Supports both:
  - New asymmetric signing keys (ES256/RS256) via JWKS discovery endpoint
  - Legacy HS256 shared secret (fallback)

All signup/login/password-reset is handled client-side by @supabase/supabase-js.
The backend only verifies incoming Supabase JWT tokens.
"""
import os
import time
import threading
from typing import Optional, Dict
from jose import jwt, JWTError
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# JWKS cache (refreshed every 10 minutes)
_jwks_cache: Dict = {}
_jwks_cache_time: float = 0
_jwks_lock = threading.Lock()
_JWKS_CACHE_TTL = 600  # 10 minutes


def _get_jwks() -> Dict:
    """Fetch and cache the JWKS from Supabase's discovery endpoint."""
    global _jwks_cache, _jwks_cache_time

    now = time.time()
    if _jwks_cache and (now - _jwks_cache_time) < _JWKS_CACHE_TTL:
        return _jwks_cache

    with _jwks_lock:
        # Double-check after acquiring lock
        if _jwks_cache and (time.time() - _jwks_cache_time) < _JWKS_CACHE_TTL:
            return _jwks_cache

        if not SUPABASE_URL:
            return {}

        url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            _jwks_cache_time = time.time()
            return _jwks_cache
        except Exception as e:
            print(f"WARNING: Failed to fetch JWKS from {url}: {e}")
            return _jwks_cache  # return stale cache if available


def _get_signing_key_from_jwks(token: str) -> Optional[Dict]:
    """
    Extract the signing key from JWKS that matches the token's 'kid' header.
    Returns the JWK dict or None.
    """
    jwks = _get_jwks()
    if not jwks or "keys" not in jwks:
        return None

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        return None

    kid = unverified_header.get("kid")
    alg = unverified_header.get("alg", "")

    for key in jwks["keys"]:
        if key.get("kid") == kid:
            return key

    # If no kid match, return the first key that matches the algorithm
    for key in jwks["keys"]:
        key_alg = key.get("alg", "")
        if key_alg == alg:
            return key

    return None


def verify_token(token: str) -> Optional[Dict]:
    """
    Verify a Supabase JWT access token.

    Tries JWKS-based verification first (ES256/RS256), then falls back
    to the legacy HS256 shared secret if configured.

    Returns the decoded payload or None if invalid/expired.
    """
    # Strategy 1: JWKS-based verification (asymmetric keys)
    if SUPABASE_URL:
        jwk = _get_signing_key_from_jwks(token)
        if jwk:
            try:
                unverified_header = jwt.get_unverified_header(token)
                alg = unverified_header.get("alg", "ES256")
                payload = jwt.decode(
                    token,
                    jwk,
                    algorithms=[alg],
                    options={"verify_aud": False},
                )
                return payload
            except JWTError:
                pass  # fall through to legacy

    # Strategy 2: Legacy HS256 shared secret
    if SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return payload
        except JWTError:
            pass

    return None
