"""
Security Utilities

Password hashing and JWT token management.
"""

import secrets
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ═══════════════════════════════════════════════════════════
# PASSWORD HASHING
# ═══════════════════════════════════════════════════════════

# Password context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string

    Example:
        hashed = hash_password("mypassword123")
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password

    Returns:
        True if password matches, False otherwise

    Example:
        if verify_password("mypassword123", user.password_hash):
            # Password is correct
    """
    return pwd_context.verify(plain_password, hashed_password)


# ═══════════════════════════════════════════════════════════
# JWT TOKEN MANAGEMENT
# ═══════════════════════════════════════════════════════════

class TokenType:
    """Token type constants."""
    ACCESS = "access"
    REFRESH = "refresh"


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Example:
        token = create_access_token(
            data={"sub": str(user.user_id), "username": user.username}
        )
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": TokenType.ACCESS,
        "jti": generate_token_id(),
    })

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Payload data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string

    Example:
        refresh_token = create_refresh_token(data={"sub": str(user.user_id)})
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

    # Only generate JTI if not already provided
    if "jti" not in to_encode:
        to_encode["jti"] = generate_token_id()

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": TokenType.REFRESH,
    })

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired

    Example:
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
        except JWTError:
            raise TokenInvalidException()
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def verify_token(token: str, expected_type: str = TokenType.ACCESS) -> dict[str, Any] | None:
    """
    Verify a JWT token and check its type.

    Args:
        token: JWT token string
        expected_type: Expected token type (access or refresh)

    Returns:
        Decoded payload if valid, None if invalid

    Example:
        payload = verify_token(token, TokenType.ACCESS)
        if payload is None:
            raise TokenInvalidException()
    """
    try:
        payload = decode_token(token)
        token_type = payload.get("type")

        if token_type != expected_type:
            return None

        return payload
    except JWTError:
        return None


def generate_token_id() -> str:
    """
    Generate a unique token ID (jti claim).

    Returns:
        Random URL-safe string for token identification
    """
    return secrets.token_urlsafe(32)


def generate_session_token() -> str:
    """
    Generate a unique session token.

    Returns:
        Random URL-safe string for session identification
    """
    return secrets.token_urlsafe(64)


def generate_password_reset_token() -> str:
    """
    Generate a token for password reset.

    Returns:
        Random URL-safe string for password reset
    """
    return secrets.token_urlsafe(32)


# ═══════════════════════════════════════════════════════════
# TOKEN EXTRACTION
# ═══════════════════════════════════════════════════════════

def extract_token_from_header(authorization: str | None) -> str | None:
    """
    Extract bearer token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Token string if valid Bearer format, None otherwise

    Example:
        token = extract_token_from_header("Bearer eyJhbGciOiJIUzI1...")
    """
    if authorization is None:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


# ═══════════════════════════════════════════════════════════
# TOKEN PAYLOAD HELPERS
# ═══════════════════════════════════════════════════════════

def get_token_expiry(token: str) -> datetime | None:
    """
    Get expiration time from a token.

    Args:
        token: JWT token string

    Returns:
        Expiration datetime if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp)
        return None
    except JWTError:
        return None


def is_token_expired(token: str) -> bool:
    """
    Check if a token has expired.

    Args:
        token: JWT token string

    Returns:
        True if expired or invalid, False otherwise
    """
    expiry = get_token_expiry(token)
    if expiry is None:
        return True
    return datetime.utcnow() > expiry
