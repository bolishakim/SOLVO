"""
Core Application Module

Authentication, user management, sessions, and audit logging.
"""

from app.core.models import (
    User,
    Role,
    UserRole,
    UserSession,
    TwoFactorAuth,
    Workflow,
    AuditLog,
    DataExport,
)
from app.core.routers import auth_router
from app.core.dependencies import (
    get_current_user,
    get_current_active_user,
    require_role,
    require_any_role,
    require_admin,
    CurrentUser,
    ActiveUser,
    OptionalUser,
)

__all__ = [
    # Models
    "User",
    "Role",
    "UserRole",
    "UserSession",
    "TwoFactorAuth",
    "Workflow",
    "AuditLog",
    "DataExport",
    # Routers
    "auth_router",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "require_any_role",
    "require_admin",
    "CurrentUser",
    "ActiveUser",
    "OptionalUser",
]
