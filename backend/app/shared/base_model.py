"""
Base Model with Common Fields

Provides mixins and base classes for SQLAlchemy models
with automatic timestamp handling.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at columns to a model.

    Usage:
        class User(Base, TimestampMixin):
            __tablename__ = "users"
            ...
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.

    Instead of deleting records, sets is_deleted to True.

    Usage:
        class Document(Base, SoftDeleteMixin):
            __tablename__ = "documents"
            ...
    """

    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class AuditMixin:
    """
    Mixin for tracking who created/updated a record.

    Note: created_by and updated_by store user IDs.
    The foreign key relationship should be defined in the model.

    Usage:
        class WeighSlip(Base, TimestampMixin, AuditMixin):
            __tablename__ = "weigh_slips"
            ...
    """

    created_by: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    updated_by: Mapped[int | None] = mapped_column(
        nullable=True,
    )


def model_to_dict(model: Any, exclude: set | None = None) -> dict:
    """
    Convert SQLAlchemy model instance to dictionary.

    Args:
        model: SQLAlchemy model instance
        exclude: Set of field names to exclude

    Returns:
        Dictionary representation of the model
    """
    exclude = exclude or set()
    return {
        c.name: getattr(model, c.name)
        for c in model.__table__.columns
        if c.name not in exclude
    }
