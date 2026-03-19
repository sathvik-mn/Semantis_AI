"""
Encryption module for securely storing OpenAI API keys.
Uses Fernet (symmetric encryption) for API key storage.
"""
import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

log = logging.getLogger(__name__)

# Get encryption key from environment or generate a default (for development)
ENCRYPTION_KEY_ENV = os.getenv("ENCRYPTION_KEY")
ENCRYPTION_SALT_ENV = os.getenv("ENCRYPTION_SALT")


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


