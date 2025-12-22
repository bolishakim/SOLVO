"""
Core App Schemas

Pydantic schemas for request/response validation.
"""

from app.core.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    TokenPayload,
)
from app.core.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # Auth schemas
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "RegisterRequest",
    "TokenPayload",
    # User schemas
    "UserCreate",
    "UserResponse",
    "UserUpdate",
]
