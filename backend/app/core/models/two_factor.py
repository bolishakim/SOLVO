"""
Two-Factor Authentication Model

Stores TOTP secrets and 2FA settings for users.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, SchemaNames

if TYPE_CHECKING:
    from app.core.models.user import User


class TwoFactorAuth(Base):
    """
    Two-Factor Authentication settings for users.

    Stores the TOTP secret key (encrypted) and 2FA status.
    Each user can have at most one 2FA configuration.
    """

    __tablename__ = "two_factor_auth"
    __table_args__ = {"schema": SchemaNames.CORE_APP}

    # ─── Primary Key ───────────────────────────────────────
    tfa_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Foreign Key ───────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SchemaNames.CORE_APP}.users.user_id", ondelete="CASCADE"),
        unique=True,  # One-to-one relationship
        nullable=False,
        index=True,
    )

    # ─── 2FA Fields ────────────────────────────────────────
    secret_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Encrypted TOTP secret key for authenticator apps",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether 2FA is currently active for this user",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether user has verified 2FA setup with a valid code",
    )

    # ─── Backup Codes ──────────────────────────────────────
    backup_codes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Comma-separated list of hashed backup codes",
    )

    # ─── Timestamps ────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    enabled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When 2FA was enabled",
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time 2FA was used for login",
    )

    # ─── Relationships ─────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="two_factor_auth",
    )

    def __repr__(self) -> str:
        return f"<TwoFactorAuth(tfa_id={self.tfa_id}, user_id={self.user_id}, enabled={self.is_enabled})>"
