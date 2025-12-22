"""
Authentication Schemas

Request and response schemas for authentication endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.shared.validators import validate_password, validate_username


# ═══════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════


class RegisterRequest(BaseModel):
    """Schema for user registration request."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (3-50 chars, alphanumeric with underscore/hyphen)",
        examples=["john_doe"],
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address",
        examples=["john.doe@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, uppercase, lowercase, digit)",
        examples=["SecurePass123"],
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="First name",
        examples=["John"],
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Last name",
        examples=["Doe"],
    )
    phone_number: str | None = Field(
        default=None,
        max_length=20,
        description="Optional phone number",
        examples=["+43 123 456 7890"],
    )

    @field_validator("username")
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        valid, error = validate_username(v)
        if not valid:
            raise ValueError(error)
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        valid, error = validate_password(v)
        if not valid:
            raise ValueError(error)
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class LoginRequest(BaseModel):
    """Schema for user login request."""

    username_or_email: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Username or email address",
        examples=["john_doe", "john.doe@example.com"],
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User password",
    )


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="Valid refresh token",
    )


class TwoFactorLoginRequest(BaseModel):
    """Schema for 2FA verification during login."""

    temp_token: str = Field(
        ...,
        description="Temporary token from initial login",
    )
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit TOTP code",
        examples=["123456"],
    )

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Code must contain only digits")
        return v


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""

    current_password: str = Field(
        ...,
        min_length=1,
        description="Current password",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        valid, error = validate_password(v)
        if not valid:
            raise ValueError(error)
        return v


class LogoutRequest(BaseModel):
    """Schema for logout request."""

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="Refresh token to invalidate",
    )


class LogoutAllRequest(BaseModel):
    """Schema for logout all sessions request."""

    keep_current: bool = Field(
        default=False,
        description="Keep the current session active",
    )
    current_refresh_token: str | None = Field(
        default=None,
        description="Current refresh token (required if keep_current is True)",
    )


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""

    email: EmailStr = Field(
        ...,
        description="Email address associated with the account",
        examples=["john.doe@example.com"],
    )


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request."""

    token: str = Field(
        ...,
        min_length=1,
        description="Password reset token",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        valid, error = validate_password(v)
        if not valid:
            raise ValueError(error)
        return v


# ═══════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str = Field(..., description="Subject (user ID)")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email")
    roles: list[str] = Field(default_factory=list, description="User roles")
    type: str = Field(..., description="Token type (access/refresh)")
    jti: str = Field(..., description="Token ID")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")


class TokenPair(BaseModel):
    """Schema for access and refresh token pair."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")


class LoginResponse(BaseModel):
    """Schema for successful login response."""

    success: bool = Field(default=True)
    message: str = Field(default="Login successful")
    data: dict[str, Any] = Field(..., description="Response data")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Login successful",
                "data": {
                    "user": {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "username": "john_doe",
                        "email": "john.doe@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "roles": ["Standard User"],
                    },
                    "tokens": {
                        "access_token": "eyJhbGciOiJIUzI1NiIs...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                    },
                },
            }
        }


class TwoFactorRequiredResponse(BaseModel):
    """Schema for response when 2FA is required."""

    success: bool = Field(default=True)
    message: str = Field(default="Two-factor authentication required")
    data: dict[str, Any] = Field(..., description="Response data")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Two-factor authentication required",
                "data": {
                    "requires_2fa": True,
                    "temp_token": "temp_abc123...",
                },
            }
        }


class RefreshTokenResponse(BaseModel):
    """Schema for token refresh response."""

    success: bool = Field(default=True)
    message: str = Field(default="Token refreshed successfully")
    data: dict[str, Any] = Field(..., description="Response data")


class SessionValidateResponse(BaseModel):
    """Schema for session validation response."""

    success: bool = Field(default=True)
    data: dict[str, Any] = Field(..., description="Session info")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "valid": True,
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "john_doe",
                    "roles": ["Standard User"],
                    "session_expires_at": "2024-12-25T12:00:00Z",
                },
            }
        }
