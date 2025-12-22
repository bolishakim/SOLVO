"""
Role Models

Role and UserRole models for role-based access control (RBAC).
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, SchemaNames

if TYPE_CHECKING:
    from app.core.models.user import User


class Role(Base):
    """
    Role model for access control.

    Predefined roles:
    - Admin: Full system access, can see all projects and data
    - Standard User: Limited access, can only see assigned projects
    - Viewer: Read-only access to assigned projects
    """

    __tablename__ = "roles"
    __table_args__ = {"schema": SchemaNames.CORE_APP}

    # ─── Primary Key ───────────────────────────────────────
    role_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Role Fields ───────────────────────────────────────
    role_name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    role_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Machine-readable role identifier (e.g., 'admin', 'standard_user')",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # ─── Timestamps ────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ─── Relationships ─────────────────────────────────────
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Role(role_id={self.role_id}, role_name='{self.role_name}')>"


class UserRole(Base):
    """
    User-Role association table.

    Many-to-many relationship between users and roles.
    Tracks who assigned the role and when.
    """

    __tablename__ = "user_roles"
    __table_args__ = {"schema": SchemaNames.CORE_APP}

    # ─── Composite Primary Key ─────────────────────────────
    user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SchemaNames.CORE_APP}.users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SchemaNames.CORE_APP}.roles.role_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # ─── Assignment Tracking ───────────────────────────────
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    assigned_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey(f"{SchemaNames.CORE_APP}.users.user_id", ondelete="SET NULL"),
        nullable=True,
        doc="User ID of admin who assigned this role",
    )

    # ─── Relationships ─────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_roles",
        foreign_keys=[user_id],
    )
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="user_roles",
    )

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


# ─── Role Constants ────────────────────────────────────────

class RoleNames:
    """Constants for role names."""
    ADMIN = "Admin"
    STANDARD_USER = "Standard User"
    VIEWER = "Viewer"


class RoleCodes:
    """Constants for role codes (machine-readable identifiers)."""
    ADMIN = "admin"
    STANDARD_USER = "standard_user"
    VIEWER = "viewer"


# Default roles to seed
DEFAULT_ROLES = [
    {
        "role_name": RoleNames.ADMIN,
        "role_code": RoleCodes.ADMIN,
        "description": "Full system access - can see all projects and data",
    },
    {
        "role_name": RoleNames.STANDARD_USER,
        "role_code": RoleCodes.STANDARD_USER,
        "description": "Limited access - can only see assigned projects",
    },
    {
        "role_name": RoleNames.VIEWER,
        "role_code": RoleCodes.VIEWER,
        "description": "Read-only access to assigned projects",
    },
]
