"""
User Model

Core user model for authentication and user management.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, SchemaNames
from app.shared.base_model import TimestampMixin

if TYPE_CHECKING:
    from app.core.models.role import UserRole
    from app.core.models.session import UserSession
    from app.core.models.two_factor import TwoFactorAuth


class User(Base, TimestampMixin):
    """
    User model for authentication and authorization.

    Stores user credentials and profile information.
    Passwords are stored as bcrypt hashes.
    """

    __tablename__ = "users"
    __table_args__ = {"schema": SchemaNames.CORE_APP}

    # ─── Primary Key ───────────────────────────────────────
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Authentication Fields ─────────────────────────────
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password",
    )

    # ─── Profile Fields ────────────────────────────────────
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    # ─── Status Fields ─────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Email verification status",
    )
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether 2FA is enabled for this user",
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )

    # ─── Security Fields ───────────────────────────────────
    failed_login_attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        doc="Account locked until this time after too many failed attempts",
    )

    # ─── Relationships ─────────────────────────────────────
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="[UserRole.user_id]",
    )

    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    two_factor_auth: Mapped[Optional["TwoFactorAuth"]] = relationship(
        "TwoFactorAuth",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # ─── Properties ────────────────────────────────────────
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    @property
    def roles(self) -> List[str]:
        """Get list of role names assigned to user."""
        return [ur.role.role_name for ur in self.user_roles]

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return role_name in self.roles

    def is_admin(self) -> bool:
        """Check if user has Admin role."""
        return self.has_role("Admin")

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, username='{self.username}', email='{self.email}')>"
