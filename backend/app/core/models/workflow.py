"""
Workflow Model

Registry of available workflows in the system.
Each workflow corresponds to a separate database schema.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, SchemaNames


class Workflow(Base):
    """
    Workflow registry model.

    Tracks available workflows in the multi-workflow system.
    Each workflow has its own database schema.

    Examples:
    - Landfill Document Management (landfill_mgmt schema)
    - Equipment Tracking (future)
    - Employee Time Tracking (future)
    """

    __tablename__ = "workflows"
    __table_args__ = {"schema": SchemaNames.CORE_APP}

    # ─── Primary Key ───────────────────────────────────────
    workflow_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── Workflow Fields ───────────────────────────────────
    workflow_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Human-readable workflow name",
    )
    workflow_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique code for the workflow (e.g., 'landfill_mgmt')",
    )
    schema_name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        doc="PostgreSQL schema name for this workflow",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # ─── Status ────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this workflow is currently active",
    )

    # ─── Timestamps ────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Workflow(workflow_id={self.workflow_id}, code='{self.workflow_code}', active={self.is_active})>"


# ─── Default Workflows ─────────────────────────────────────

DEFAULT_WORKFLOWS = [
    {
        "workflow_name": "Landfill Document Management",
        "workflow_code": "landfill_mgmt",
        "schema_name": "landfill_mgmt",
        "description": "Automated waste tracking from PDF documents for construction sites",
        "is_active": True,
    },
]
