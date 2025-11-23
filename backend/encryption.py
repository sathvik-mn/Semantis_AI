"""
Encryption module for securely storing OpenAI API keys.
Uses Fernet (symmetric encryption) for API key storage.
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Get encryption key from environment or generate a default (for development)
ENCRYPTION_KEY_ENV = os.getenv("ENCRYPTION_KEY")

def _get_encryption_key() -> bytes:
    """
    Get or generate encryption key.
    
    In production, ENCRYPTION_KEY should be set as a base64-encoded Fernet key.
    For development, generates a key from a default password.
    
    Returns:
        Fernet encryption key bytes
    """
    if ENCRYPTION_KEY_ENV:
        try:
            # Try to use provided key directly (should be base64-encoded Fernet key)
            return base64.urlsafe_b64decode(ENCRYPTION_KEY_ENV.encode())
        except Exception:
            # If not valid Fernet key, derive from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'semantis_ai_salt',  # In production, use random salt
                iterations=100000,
            )
            return base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY_ENV.encode()))
    else:
        # Development: derive from default password
        # WARNING: In production, always set ENCRYPTION_KEY environment variable!
        default_password = os.getenv("DEFAULT_ENCRYPTION_PASSWORD", "change-me-in-production")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'semantis_ai_salt',
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

