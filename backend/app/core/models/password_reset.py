"""
Password Reset Token Model

Model for secure password reset tokens.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, SchemaNames
from app.shared.base_model import TimestampMixin

if TYPE_CHECKING:
    from app.core.models.user import User


class PasswordResetToken(Base, TimestampMixin):
    """
    Password reset token model.

    Stores tokens for password reset requests.
    Tokens are single-use and expire after a configurable time.
    """

    __tablename__ = "password_reset_tokens"
    __table_args__ = {"schema": SchemaNames.CORE_APP}

    # ─── Primary Key ───────────────────────────────────────
    token_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Foreign Keys ──────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SchemaNames.CORE_APP}.users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Token Fields ──────────────────────────────────────
    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="SHA-256 hash of the reset token",
    )
    expires_at: Mapped[datetime] = mapped_column(
        nullable=False,
        doc="Token expiration time",
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the token has been used",
    )
    used_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        doc="When the token was used",
    )

    # ─── Request Context ───────────────────────────────────
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        doc="IP address that requested the reset",
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="User agent that requested the reset",
    )

    # ─── Relationships ─────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )

    # ─── Properties ────────────────────────────────────────
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired and not self.is_used

    def __repr__(self) -> str:
        return f"<PasswordResetToken(token_id={self.token_id}, user_id={self.user_id}, is_used={self.is_used})>"
