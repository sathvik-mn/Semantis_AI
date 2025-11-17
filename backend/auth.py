"""
Authentication module for JWT tokens and password hashing.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
import bcrypt
from jose import JWTError, jwt

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)

    if not has_letter:
        return False, "Password must contain at least one letter"

    if not has_number:
        return False, "Password must contain at least one number"

    return True, ""

def validate_email(email: str) -> tuple[bool, str]:
    """
    Basic email validation.

    Args:
        email: Email to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or '@' not in email:
        return False, "Invalid email format"

    if len(email) < 3:
        return False, "Email is too short"

    parts = email.split('@')
    if len(parts) != 2:
        return False, "Invalid email format"

    if not parts[0] or not parts[1]:
        return False, "Invalid email format"

    if '.' not in parts[1]:
        return False, "Invalid email domain"

    return True, ""
