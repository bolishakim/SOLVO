"""
User Session Model

Tracks active user sessions for authentication and security.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, SchemaNames

if TYPE_CHECKING:
    from app.core.models.user import User


class UserSession(Base):
    """
    User session model for tracking active sessions.

    Stores session tokens, IP addresses, and expiration times.
    Used for:
    - Session validation on each request
    - Viewing active sessions
    - Revoking sessions (logout from specific device)
    - Security auditing
    """

    __tablename__ = "user_sessions"
    __table_args__ = {"schema": SchemaNames.CORE_APP}

    # ─── Primary Key ───────────────────────────────────────
    session_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Foreign Key ───────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SchemaNames.CORE_APP}.users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Session Fields ────────────────────────────────────
    session_token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique session identifier (JWT jti claim)",
    )
    refresh_token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Refresh token for obtaining new access tokens",
    )

    # ─── Client Information ────────────────────────────────
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        doc="Client IP address at session creation",
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Client user agent string",
    )

    # ─── Timestamps ────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Session expiration time",
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Last time this session was used",
    )

    # ─── Status ────────────────────────────────────────────
    is_revoked: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        doc="True if session was explicitly revoked (logout)",
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ─── Relationships ─────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="sessions",
    )

    # ─── Properties ────────────────────────────────────────
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)

    @property
    def is_valid(self) -> bool:
        """Check if session is still valid (not expired and not revoked)."""
        return not self.is_expired and not self.is_revoked

    def __repr__(self) -> str:
        return f"<UserSession(session_id={self.session_id}, user_id={self.user_id}, valid={self.is_valid})>"
