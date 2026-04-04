"""
Encryption module for securely storing OpenAI API keys and cache entries.
- Fernet (symmetric) for API key storage
- AES-256-GCM with per-tenant key derivation for cache entry encryption
"""
import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

log = logging.getLogger(__name__)

# Get encryption key from environment or generate a default (for development)
ENCRYPTION_KEY_ENV = os.getenv("ENCRYPTION_KEY")
ENCRYPTION_SALT_ENV = os.getenv("ENCRYPTION_SALT")


def is_api_key_encryption_configured() -> bool:
    """Require explicit encryption config before accepting user-supplied API keys."""
    return bool(ENCRYPTION_KEY_ENV and ENCRYPTION_SALT_ENV)


def _get_salt() -> bytes:
    """
    Get the PBKDF2 salt from the ENCRYPTION_SALT env var.

    For production, generate a random 16-byte salt once per deployment and
    store it in ENCRYPTION_SALT as a hex string:
        python -c "import os; print(os.urandom(16).hex())"

    If the env var is missing, falls back to a static dev-only salt and logs
    a warning.
    """
    if ENCRYPTION_SALT_ENV:
        return bytes.fromhex(ENCRYPTION_SALT_ENV)
    log.warning(
        "ENCRYPTION_SALT not set — using static dev salt. "
        "Set ENCRYPTION_SALT to a random hex string for production."
    )
    return b'semantis_dev_salt_do_not_use_in_prod'


def _get_encryption_key() -> bytes:
    """
    Get or generate encryption key.

    In production, ENCRYPTION_KEY should be set as a base64-encoded Fernet key.
    For development, generates a key from a default password.

    Returns:
        Fernet encryption key bytes
    """
    salt = _get_salt()

    if ENCRYPTION_KEY_ENV:
        try:
            # Try to use provided key directly (should be base64-encoded Fernet key)
            key = base64.urlsafe_b64decode(ENCRYPTION_KEY_ENV.encode())
            if len(key) == 32:
                return base64.urlsafe_b64encode(key)
            return key
        except Exception:
            # If not valid Fernet key, derive from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            return base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY_ENV.encode()))
    else:
        # Development: derive from default password
        log.warning(
            "ENCRYPTION_KEY not set — using default dev password. "
            "Set ENCRYPTION_KEY for production."
        )
        default_password = os.getenv("DEFAULT_ENCRYPTION_PASSWORD", "change-me-in-production")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(default_password.encode()))
        return key

# Initialize Fernet cipher
_fernet = None

def _get_fernet() -> Fernet:
    """Get Fernet cipher instance."""
    global _fernet
    if _fernet is None:
        key = _get_encryption_key()
        _fernet = Fernet(key)
    return _fernet

def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an OpenAI API key.
    
    Args:
        api_key: Plain text OpenAI API key
    
    Returns:
        Encrypted key string (base64-encoded)
    
    Raises:
        ValueError: If API key format is invalid
    """
    # Validate OpenAI API key format (starts with sk-)
    if not api_key or not api_key.startswith('sk-'):
        raise ValueError("Invalid OpenAI API key format. Must start with 'sk-'")
    
    fernet = _get_fernet()
    encrypted = fernet.encrypt(api_key.encode('utf-8'))
    return encrypted.decode('utf-8')

def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt an OpenAI API key.
    
    Args:
        encrypted_key: Encrypted key string
    
    Returns:
        Plain text OpenAI API key
    
    Raises:
        ValueError: If decryption fails (invalid key or corrupted data)
    """
    if not encrypted_key:
        raise ValueError("Encrypted key is empty")
    
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_key.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decrypt API key: {str(e)}")


# ==========================================================================
# Cache Entry Encryption (AES-256-GCM, per-tenant keys)
# ==========================================================================

CACHE_MASTER_KEY_ENV = "CACHE_ENCRYPTION_KEY"
_cache_master_key: Optional[bytes] = None


def _get_cache_master_key() -> Optional[bytes]:
    """Load cache encryption master key from env. Returns None if not configured."""
    global _cache_master_key
    if _cache_master_key is not None:
        return _cache_master_key

    raw = os.getenv(CACHE_MASTER_KEY_ENV, "").strip()
    if not raw:
        return None

    try:
        if len(raw) == 64:
            _cache_master_key = bytes.fromhex(raw)
        else:
            _cache_master_key = base64.b64decode(raw)
        if len(_cache_master_key) != 32:
            log.error(f"CACHE_ENCRYPTION_KEY must be 32 bytes, got {len(_cache_master_key)}")
            _cache_master_key = None
            return None
        log.info("Cache encryption master key loaded")
        return _cache_master_key
    except Exception as e:
        log.error(f"Failed to parse CACHE_ENCRYPTION_KEY: {e}")
        _cache_master_key = None
        return None


def is_cache_encryption_enabled() -> bool:
    """Check if cache entry encryption is configured."""
    return _get_cache_master_key() is not None


def _derive_tenant_key(tenant_id: str) -> bytes:
    """Derive a per-tenant AES-256 key using HKDF."""
    master = _get_cache_master_key()
    if not master:
        raise RuntimeError("Cache encryption master key not available")

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"semantis-cache-v1",
        info=tenant_id.encode("utf-8"),
    )
    return hkdf.derive(master)


def encrypt_cache_entry(plaintext: str, tenant_id: str) -> str:
    """
    Encrypt cache entry text with per-tenant AES-256-GCM.
    Returns base64-encoded: nonce(12) + ciphertext + tag(16).
    Returns original text if encryption not enabled.
    """
    if not is_cache_encryption_enabled():
        return plaintext

    key = _derive_tenant_key(tenant_id)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return "ENC:" + base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_cache_entry(text: str, tenant_id: str) -> str:
    """
    Decrypt AES-256-GCM encrypted cache entry.
    Backward compatible: returns plaintext as-is if not encrypted.
    Encrypted values are prefixed with 'ENC:'.
    """
    if not text.startswith("ENC:"):
        return text

    if not is_cache_encryption_enabled():
        log.warning("Encrypted cache entry found but CACHE_ENCRYPTION_KEY not set")
        return text

    try:
        raw = base64.b64decode(text[4:])
    except Exception:
        return text

    if len(raw) < 29:  # 12 nonce + 1 data + 16 tag
        return text

    key = _derive_tenant_key(tenant_id)
    aesgcm = AESGCM(key)
    nonce = raw[:12]
    ciphertext = raw[12:]
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as e:
        log.warning(f"Cache decryption failed for tenant {tenant_id}, treating as cache miss: {e}")
        return ""


def generate_cache_encryption_key() -> str:
    """Generate a new random 256-bit key (hex-encoded). Run once for setup."""
    return os.urandom(32).hex()
