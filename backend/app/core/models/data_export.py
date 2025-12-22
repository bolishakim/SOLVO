"""
Data Export Model

Tracks exported files for download and automatic cleanup.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, SchemaNames


class ExportType(str, Enum):
    """Supported export file types."""
    EXCEL = "EXCEL"
    PDF = "PDF"
    CSV = "CSV"


class ExportStatus(str, Enum):
    """Export job status."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class DataExport(Base):
    """
    Data export tracking model.

    Tracks exported files, their filters, and expiration.
    Files are automatically cleaned up after expiration.
    """

    __tablename__ = "data_exports"
    __table_args__ = {"schema": SchemaNames.CORE_APP}

    # ─── Primary Key ───────────────────────────────────────
    export_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ─── User Reference ────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SchemaNames.CORE_APP}.users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ─── Export Details ────────────────────────────────────
    workflow_schema: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Schema from which data was exported",
    )
    export_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Type of export file (EXCEL, PDF, CSV)",
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Generated filename",
    )
    file_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Path to the exported file on disk",
    )
    file_size_bytes: Mapped[int | None] = mapped_column(
        nullable=True,
        doc="Size of exported file in bytes",
    )

    # ─── Export Parameters ─────────────────────────────────
    filters_applied: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        doc="JSON object containing filters used for export",
    )
    record_count: Mapped[int | None] = mapped_column(
        nullable=True,
        doc="Number of records exported",
    )

    # ─── Status ────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20),
        default=ExportStatus.PENDING.value,
        nullable=False,
        doc="Current status of the export job",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if export failed",
    )

    # ─── Timestamps ────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When the export file will be automatically deleted",
    )
    downloaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the file was last downloaded",
    )

    # ─── Properties ────────────────────────────────────────
    @property
    def is_expired(self) -> bool:
        """Check if export has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)

    @property
    def is_downloadable(self) -> bool:
        """Check if export can be downloaded."""
        return (
            self.status == ExportStatus.COMPLETED.value
            and not self.is_expired
        )

    def __repr__(self) -> str:
        return f"<DataExport(export_id={self.export_id}, type='{self.export_type}', status='{self.status}')>"
