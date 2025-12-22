"""
Audit Log Model

System-wide audit trail for tracking all user actions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, SchemaNames


class ActionType(str, Enum):
    """Types of actions that can be logged."""
    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"

    # CRUD Operations
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

    # Specific Actions
    REGISTER = "REGISTER"
    PASSWORD_RESET = "PASSWORD_RESET"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"

    # 2FA
    TWO_FACTOR_ENABLE = "TWO_FACTOR_ENABLE"
    TWO_FACTOR_DISABLE = "TWO_FACTOR_DISABLE"
    TWO_FACTOR_VERIFY = "TWO_FACTOR_VERIFY"

    # Roles
    ROLE_ASSIGN = "ROLE_ASSIGN"
    ROLE_REMOVE = "ROLE_REMOVE"

    # Sessions
    SESSION_REVOKE = "SESSION_REVOKE"
    SESSION_REVOKE_ALL = "SESSION_REVOKE_ALL"

    # Data Operations
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    ASSIGN = "ASSIGN"
    UNASSIGN = "UNASSIGN"


class EntityType(str, Enum):
    """Types of entities that can be audited."""
    USER = "USER"
    ROLE = "ROLE"
    SESSION = "SESSION"
    TWO_FACTOR = "TWO_FACTOR"
    WORKFLOW = "WORKFLOW"

    # Landfill workflow entities
    CONSTRUCTION_SITE = "CONSTRUCTION_SITE"
    WEIGH_SLIP = "WEIGH_SLIP"
    HAZARDOUS_SLIP = "HAZARDOUS_SLIP"
    PDF_DOCUMENT = "PDF_DOCUMENT"
    LANDFILL_COMPANY = "LANDFILL_COMPANY"
    LANDFILL_LOCATION = "LANDFILL_LOCATION"
    MATERIAL_TYPE = "MATERIAL_TYPE"

    # Export
    DATA_EXPORT = "DATA_EXPORT"


class AuditLog(Base):
    """
    Audit log model for tracking all user actions.

    Provides complete audit trail for compliance and security.
    Stores old/new values for data changes.
    """

    __tablename__ = "audit_logs"
    __table_args__ = {"schema": SchemaNames.CORE_APP}

    # ─── Primary Key ───────────────────────────────────────
    log_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # ─── User Reference ────────────────────────────────────
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{SchemaNames.CORE_APP}.users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="User who performed the action (null for system actions)",
    )

    # ─── Action Details ────────────────────────────────────
    workflow_schema: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Schema where action occurred (null for core_app)",
    )
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of action performed",
    )
    entity_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Type of entity affected",
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="ID of the affected entity",
    )

    # ─── Change Details ────────────────────────────────────
    changes: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        doc="JSON object with old and new values: {'old': {...}, 'new': {...}}",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Human-readable description of the action",
    )

    # ─── Request Context ───────────────────────────────────
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="X-Request-ID for request tracing",
    )

    # ─── Timestamp ─────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<AuditLog(log_id={self.log_id}, action='{self.action_type}', entity='{self.entity_type}')>"

    @classmethod
    def create_log(
        cls,
        action_type: ActionType | str,
        user_id: int | None = None,
        entity_type: EntityType | str | None = None,
        entity_id: str | int | None = None,
        workflow_schema: str | None = None,
        changes: dict | None = None,
        description: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> "AuditLog":
        """
        Factory method to create an audit log entry.

        Args:
            action_type: Type of action (use ActionType enum)
            user_id: ID of user performing action
            entity_type: Type of entity affected (use EntityType enum)
            entity_id: ID of affected entity
            workflow_schema: Schema where action occurred
            changes: Dict with 'old' and 'new' values
            description: Human-readable description
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request ID for tracing

        Returns:
            AuditLog instance (not yet persisted)
        """
        return cls(
            user_id=user_id,
            action_type=action_type.value if isinstance(action_type, ActionType) else action_type,
            entity_type=entity_type.value if isinstance(entity_type, EntityType) else entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            workflow_schema=workflow_schema,
            changes=changes,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
