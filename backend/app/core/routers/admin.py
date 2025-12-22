"""
Admin Router

Admin-only endpoints for user and role management.
"""

from typing import Annotated, Any

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.models import User, Role, UserRole
from app.core.schemas.user import (
    UserWithRolesResponse,
    UserAdminUpdate,
    RoleAssignRequest,
    RoleResponse,
    RoleDetailResponse,
)
from app.core.services.user_service import UserService
from app.core.services.role_service import RoleService
from app.core.services.audit_service import AuditService
from app.core.schemas.audit import AuditLogFilter
from app.core.models.audit_log import ActionType, EntityType
from app.core.dependencies import require_admin
from app.shared.responses import success_response, paginated_response
from app.shared.pagination import PaginationParams, paginate_query
from app.shared.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/admin", tags=["Admin"])


# ═══════════════════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════════════════


@router.get(
    "/users",
    summary="List all users",
    response_description="Paginated list of users",
)
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(default=None, description="Search by username or email"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    role_code: str | None = Query(default=None, description="Filter by role code"),
) -> dict[str, Any]:
    """
    List all users with pagination and filters.

    **Requires:** Admin role

    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **search**: Search in username and email
    - **is_active**: Filter by active status
    - **role_code**: Filter by role code
    """
    # Build base query
    query = (
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .order_by(User.created_at.desc())
    )

    # Apply search filter
    if search:
        search_pattern = f"%{search.lower()}%"
        query = query.where(
            (User.username.ilike(search_pattern)) | (User.email.ilike(search_pattern))
        )

    # Apply active filter
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Apply role filter
    if role_code:
        query = query.join(UserRole).join(Role).where(Role.role_code == role_code)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    # Build response
    user_service = UserService(db)
    user_data = []
    for user in users:
        roles = user_service.get_user_roles(user)
        user_dict = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "two_factor_enabled": user.two_factor_enabled,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
            "roles": roles,
        }
        user_data.append(user_dict)

    return paginated_response(
        data=user_data,
        page=page,
        per_page=page_size,
        total_items=total,
    )


@router.get(
    "/users/{user_id}",
    summary="Get user details",
    response_description="User details with roles",
)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Get detailed information about a specific user.

    **Requires:** Admin role

    **Path Parameters:**
    - **user_id**: User ID
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    roles = user_service.get_user_roles(user)

    return success_response(
        data={
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "two_factor_enabled": user.two_factor_enabled,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
            "roles": roles,
        }
    )


@router.put(
    "/users/{user_id}",
    summary="Update user",
    response_description="Updated user",
)
async def update_user(
    user_id: int,
    request: UserAdminUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Update a user's information.

    **Requires:** Admin role

    **Path Parameters:**
    - **user_id**: User ID

    **Request Body:**
    - **first_name**: New first name (optional)
    - **last_name**: New last name (optional)
    - **phone_number**: New phone number (optional)
    - **is_active**: Account active status (optional)
    - **is_verified**: Email verification status (optional)
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    # Update fields
    if request.first_name is not None:
        user.first_name = request.first_name.strip()
    if request.last_name is not None:
        user.last_name = request.last_name.strip()
    if request.phone_number is not None:
        user.phone_number = request.phone_number
    if request.is_active is not None:
        user.is_active = request.is_active
    if request.is_verified is not None:
        user.is_verified = request.is_verified

    await db.commit()
    await db.refresh(user)

    roles = user_service.get_user_roles(user)

    return success_response(
        data={
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "two_factor_enabled": user.two_factor_enabled,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
            "roles": roles,
        },
        message="User updated successfully",
    )


@router.delete(
    "/users/{user_id}",
    summary="Deactivate user",
    response_description="User deactivated",
)
async def deactivate_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Deactivate a user account (soft delete).

    This sets `is_active` to False rather than deleting the user.
    The user can be reactivated later by updating their status.

    **Requires:** Admin role

    **Path Parameters:**
    - **user_id**: User ID

    **Note:** Admin cannot deactivate themselves.
    """
    if user_id == admin.user_id:
        raise ValidationException(message="Cannot deactivate your own account")

    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    user.is_active = False
    await db.commit()

    return success_response(
        data={"user_id": user_id, "is_active": False},
        message="User deactivated successfully",
    )


# ═══════════════════════════════════════════════════════════
# ROLE MANAGEMENT
# ═══════════════════════════════════════════════════════════


@router.get(
    "/roles",
    summary="List all roles",
    response_description="List of roles with user counts",
)
async def list_roles(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    List all available roles with user counts.

    **Requires:** Admin role
    """
    role_service = RoleService(db)
    roles = await role_service.get_all_roles()

    role_data = []
    for role in roles:
        user_count = await role_service.get_role_user_count(role.role_id)
        role_data.append({
            "role_id": role.role_id,
            "role_name": role.role_name,
            "role_code": role.role_code,
            "description": role.description,
            "user_count": user_count,
        })

    return success_response(data=role_data)


@router.get(
    "/users/{user_id}/roles",
    summary="Get user roles",
    response_description="User's roles",
)
async def get_user_roles(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Get all roles assigned to a user.

    **Requires:** Admin role

    **Path Parameters:**
    - **user_id**: User ID
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    role_service = RoleService(db)
    roles = await role_service.get_user_roles(user_id)

    role_data = [
        {
            "role_id": role.role_id,
            "role_name": role.role_name,
            "role_code": role.role_code,
        }
        for role in roles
    ]

    return success_response(data=role_data)


@router.post(
    "/users/{user_id}/roles",
    summary="Assign role to user",
    response_description="Role assigned",
)
async def assign_role(
    user_id: int,
    request: RoleAssignRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Assign a role to a user.

    **Requires:** Admin role

    **Path Parameters:**
    - **user_id**: User ID

    **Request Body:**
    - **role_id**: Role ID to assign
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    role_service = RoleService(db)
    user_role = await role_service.assign_role(
        user_id=user_id,
        role_id=request.role_id,
        assigned_by=admin.user_id,
    )

    role = await role_service.get_role_by_id(request.role_id)

    return success_response(
        data={
            "user_id": user_id,
            "role_id": role.role_id,
            "role_name": role.role_name,
            "role_code": role.role_code,
            "assigned_by": admin.user_id,
        },
        message=f"Role '{role.role_name}' assigned to user",
    )


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    summary="Remove role from user",
    response_description="Role removed",
)
async def remove_role(
    user_id: int,
    role_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Remove a role from a user.

    **Requires:** Admin role

    **Path Parameters:**
    - **user_id**: User ID
    - **role_id**: Role ID to remove

    **Note:** Users must have at least one role.
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    role_service = RoleService(db)
    role = await role_service.get_role_by_id(role_id)

    if not role:
        raise NotFoundException(message="Role not found")

    # Prevent admin from removing their own admin role
    if user_id == admin.user_id and role.role_code == "admin":
        raise ValidationException(
            message="Cannot remove admin role from yourself"
        )

    await role_service.remove_role(user_id, role_id)

    return success_response(
        data={"user_id": user_id, "role_id": role_id},
        message=f"Role '{role.role_name}' removed from user",
    )


# ═══════════════════════════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════════════════════════


@router.get(
    "/stats",
    summary="Get admin statistics",
    response_description="System statistics",
)
async def get_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Get system-wide statistics.

    **Requires:** Admin role

    **Returns:**
    - Total users
    - Active users
    - Users by role
    - Users with 2FA enabled
    """
    # Total users
    total_query = select(func.count()).select_from(User)
    total_result = await db.execute(total_query)
    total_users = total_result.scalar() or 0

    # Active users
    active_query = select(func.count()).select_from(User).where(User.is_active == True)
    active_result = await db.execute(active_query)
    active_users = active_result.scalar() or 0

    # Users with 2FA
    tfa_query = select(func.count()).select_from(User).where(User.two_factor_enabled == True)
    tfa_result = await db.execute(tfa_query)
    users_with_2fa = tfa_result.scalar() or 0

    # Users by role
    role_service = RoleService(db)
    roles = await role_service.get_all_roles()
    users_by_role = {}
    for role in roles:
        count = await role_service.get_role_user_count(role.role_id)
        users_by_role[role.role_code] = count

    return success_response(
        data={
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "users_with_2fa": users_with_2fa,
            "users_by_role": users_by_role,
        }
    )


# ═══════════════════════════════════════════════════════════
# AUDIT LOGS
# ═══════════════════════════════════════════════════════════


@router.get(
    "/audit-logs",
    summary="List audit logs",
    response_description="Paginated list of audit logs",
)
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    user_id: int | None = Query(default=None, description="Filter by user ID"),
    action_type: str | None = Query(default=None, description="Filter by action type"),
    entity_type: str | None = Query(default=None, description="Filter by entity type"),
    entity_id: str | None = Query(default=None, description="Filter by entity ID"),
    from_date: datetime | None = Query(default=None, description="Filter from date"),
    to_date: datetime | None = Query(default=None, description="Filter to date"),
    ip_address: str | None = Query(default=None, description="Filter by IP address"),
) -> dict[str, Any]:
    """
    List audit logs with optional filters.

    **Requires:** Admin role

    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 50, max: 100)
    - **user_id**: Filter by user who performed the action
    - **action_type**: Filter by action type (LOGIN, LOGOUT, CREATE, UPDATE, DELETE, etc.)
    - **entity_type**: Filter by entity type (USER, ROLE, SESSION, etc.)
    - **entity_id**: Filter by specific entity ID
    - **from_date**: Filter logs from this date (inclusive)
    - **to_date**: Filter logs to this date (inclusive)
    - **ip_address**: Filter by IP address
    """
    audit_service = AuditService(db)

    # Build filter
    filters = AuditLogFilter(
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        from_date=from_date,
        to_date=to_date,
        ip_address=ip_address,
    )

    logs, total = await audit_service.get_audit_logs(
        filters=filters,
        page=page,
        page_size=page_size,
    )

    # Enrich with usernames
    log_data = await audit_service.enrich_logs_with_usernames(logs)

    return paginated_response(
        data=log_data,
        page=page,
        per_page=page_size,
        total_items=total,
    )


@router.get(
    "/audit-logs/stats",
    summary="Get audit log statistics",
    response_description="Audit log statistics",
)
async def get_audit_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
    from_date: datetime | None = Query(default=None, description="Stats from date"),
    to_date: datetime | None = Query(default=None, description="Stats to date"),
) -> dict[str, Any]:
    """
    Get audit log statistics.

    **Requires:** Admin role

    **Query Parameters:**
    - **from_date**: Calculate stats from this date
    - **to_date**: Calculate stats to this date

    **Returns:**
    - Total log count
    - Counts by action type
    - Counts by entity type
    - Recent activity (last 24 hours)
    - Failed logins (last 24 hours)
    """
    audit_service = AuditService(db)

    stats = await audit_service.get_stats(
        from_date=from_date,
        to_date=to_date,
    )

    return success_response(data=stats)


@router.get(
    "/audit-logs/login-history",
    summary="Get login history",
    response_description="Login/logout history",
)
async def get_login_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
    user_id: int | None = Query(default=None, description="Filter by user ID"),
    limit: int = Query(default=50, ge=1, le=200, description="Max number of logs"),
) -> dict[str, Any]:
    """
    Get login/logout history.

    **Requires:** Admin role

    **Query Parameters:**
    - **user_id**: Filter by specific user (optional)
    - **limit**: Maximum number of logs to return (default: 50, max: 200)
    """
    audit_service = AuditService(db)
    logs = await audit_service.get_login_history(user_id=user_id, limit=limit)

    log_data = await audit_service.enrich_logs_with_usernames(logs)

    return success_response(
        data={
            "logs": log_data,
            "count": len(log_data),
        }
    )


@router.get(
    "/audit-logs/action-types",
    summary="List available action types",
    response_description="List of action types",
)
async def list_action_types(
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    List all available action types for filtering.

    **Requires:** Admin role
    """
    return success_response(
        data=[action.value for action in ActionType]
    )


@router.get(
    "/audit-logs/entity-types",
    summary="List available entity types",
    response_description="List of entity types",
)
async def list_entity_types(
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    List all available entity types for filtering.

    **Requires:** Admin role
    """
    return success_response(
        data=[entity.value for entity in EntityType]
    )


@router.get(
    "/audit-logs/user/{user_id}",
    summary="Get user audit history",
    response_description="User's audit history",
)
async def get_user_audit_history(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
    limit: int = Query(default=100, ge=1, le=500, description="Max number of logs"),
) -> dict[str, Any]:
    """
    Get audit history for a specific user (actions performed by the user).

    **Requires:** Admin role

    **Path Parameters:**
    - **user_id**: User ID

    **Query Parameters:**
    - **limit**: Maximum number of logs to return (default: 100, max: 500)
    """
    # Verify user exists
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    audit_service = AuditService(db)
    logs = await audit_service.get_user_audit_history(user_id, limit=limit)

    log_data = await audit_service.enrich_logs_with_usernames(logs)

    return success_response(
        data={
            "user_id": user_id,
            "username": user.username,
            "logs": log_data,
            "count": len(log_data),
        }
    )


@router.get(
    "/audit-logs/{log_id}",
    summary="Get audit log details",
    response_description="Audit log details",
)
async def get_audit_log(
    log_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Get detailed information about a specific audit log entry.

    **Requires:** Admin role

    **Path Parameters:**
    - **log_id**: Audit log ID
    """
    audit_service = AuditService(db)

    log = await audit_service.get_audit_log(log_id)

    if not log:
        raise NotFoundException(message="Audit log not found")

    log_data = await audit_service.enrich_log_with_username(log)

    return success_response(data=log_data)
