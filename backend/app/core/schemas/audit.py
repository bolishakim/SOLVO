"""
Audit Log Schemas

Request and response schemas for audit log operations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.models.audit_log import ActionType, EntityType


# ═══════════════════════════════════════════════════════════
# FILTER SCHEMAS
# ═══════════════════════════════════════════════════════════


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs."""

    user_id: int | None = Field(
        default=None,
        description="Filter by user ID",
    )
    action_type: str | None = Field(
        default=None,
        description="Filter by action type (LOGIN, LOGOUT, CREATE, UPDATE, DELETE, etc.)",
    )
    entity_type: str | None = Field(
        default=None,
        description="Filter by entity type (USER, ROLE, SESSION, etc.)",
    )
    entity_id: str | None = Field(
        default=None,
        description="Filter by specific entity ID",
    )
    workflow_schema: str | None = Field(
        default=None,
        description="Filter by workflow schema (core_app, landfill_mgmt, etc.)",
    )
    from_date: datetime | None = Field(
        default=None,
        description="Filter logs from this date (inclusive)",
    )
    to_date: datetime | None = Field(
        default=None,
        description="Filter logs to this date (inclusive)",
    )
    ip_address: str | None = Field(
        default=None,
        description="Filter by IP address",
    )


# ═══════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════


class AuditLogResponse(BaseModel):
    """Schema for a single audit log entry in responses."""

    log_id: int = Field(..., description="Unique audit log ID")
    user_id: int | None = Field(None, description="User who performed the action")
    username: str | None = Field(None, description="Username (if available)")
    workflow_schema: str | None = Field(None, description="Schema where action occurred")
    action_type: str = Field(..., description="Type of action performed")
    entity_type: str | None = Field(None, description="Type of entity affected")
    entity_id: str | None = Field(None, description="ID of affected entity")
    changes: dict | None = Field(None, description="Old and new values")
    description: str | None = Field(None, description="Human-readable description")
    ip_address: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="Client user agent")
    request_id: str | None = Field(None, description="Request ID for tracing")
    created_at: datetime = Field(..., description="When the action occurred")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "log_id": 123,
                "user_id": 5,
                "username": "admin",
                "workflow_schema": None,
                "action_type": "LOGIN",
                "entity_type": "USER",
                "entity_id": "5",
                "changes": None,
                "description": "User logged in successfully",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "request_id": "req-abc123",
                "created_at": "2024-12-19T10:30:00Z",
            }
        }


class AuditLogDetailResponse(BaseModel):
    """Schema for detailed audit log response (single log)."""

    success: bool = Field(default=True)
    data: AuditLogResponse


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list response."""

    success: bool = Field(default=True)
    data: list[AuditLogResponse]
    pagination: dict = Field(
        ...,
        description="Pagination info with page, per_page, total_items, total_pages",
    )


class AuditStatsResponse(BaseModel):
    """Schema for audit statistics response."""

    success: bool = Field(default=True)
    data: dict = Field(
        ...,
        description="Audit statistics including counts by action type, entity type, etc.",
    )


# ═══════════════════════════════════════════════════════════
# HELPER SCHEMAS
# ═══════════════════════════════════════════════════════════


class ActionTypeList(BaseModel):
    """Schema for listing available action types."""

    success: bool = Field(default=True)
    data: list[str] = Field(
        default_factory=lambda: [action.value for action in ActionType],
        description="List of valid action types",
    )


class EntityTypeList(BaseModel):
    """Schema for listing available entity types."""

    success: bool = Field(default=True)
    data: list[str] = Field(
        default_factory=lambda: [entity.value for entity in EntityType],
        description="List of valid entity types",
    )
