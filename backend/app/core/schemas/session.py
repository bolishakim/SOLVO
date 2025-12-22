"""
Session Schemas

Request and response schemas for session management.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════


class SessionResponse(BaseModel):
    """Schema for a single session in responses."""

    session_id: int
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    is_current: bool = Field(
        default=False,
        description="True if this is the session making the request",
    )

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Schema for session list response."""

    success: bool = Field(default=True)
    data: list[SessionResponse]
    message: str | None = None


class SessionRevokeResponse(BaseModel):
    """Schema for session revocation response."""

    success: bool = Field(default=True)
    message: str = Field(default="Session revoked successfully")
    data: dict = Field(default_factory=dict)


class SessionRevokeAllResponse(BaseModel):
    """Schema for revoking all sessions response."""

    success: bool = Field(default=True)
    message: str = Field(default="All sessions revoked successfully")
    data: dict = Field(
        default_factory=dict,
        description="Contains count of revoked sessions",
    )


# ═══════════════════════════════════════════════════════════
# INTERNAL SCHEMAS
# ═══════════════════════════════════════════════════════════


class SessionCreate(BaseModel):
    """Internal schema for creating a session."""

    user_id: int
    session_token: str
    refresh_token: str
    ip_address: str | None = None
    user_agent: str | None = None
    expires_at: datetime
