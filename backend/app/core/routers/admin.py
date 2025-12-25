"""
Admin Router

Admin-only endpoints for user and role management.
"""

from typing import Annotated, Any

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.models import User, Role, UserRole
from app.core.schemas.user import (
    UserWithRolesResponse,
    UserAdminCreate,
    UserAdminUpdate,
    RoleAssignRequest,
    RoleResponse,
    RoleDetailResponse,
)
from app.core.services.user_service import UserService
from app.core.services.role_service import RoleService
from app.core.services.audit_service import AuditService
from app.core.schemas.audit import AuditLogFilter
from app.core.models.audit_log import ActionType, EntityType, AuditLog
from app.core.dependencies import require_admin
from app.shared.responses import success_response, paginated_response
from app.shared.pagination import PaginationParams, paginate_query
from app.shared.exceptions import NotFoundException, ValidationException, ConflictException
from app.shared.security import hash_password


# ═══════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════

class AdminPasswordResetRequest(BaseModel):
    """Schema for admin password reset."""
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")


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
        # Use role codes for API consistency (role_code is used for assign/remove operations)
        roles = user_service.get_user_role_codes(user)
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


@router.post(
    "/users",
    summary="Create new user",
    response_description="Created user",
)
async def create_user(
    request: UserAdminCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Create a new user account (admin only).

    **Requires:** Admin role

    **Request Body:**
    - **username**: Username (3-50 chars, alphanumeric with underscore/hyphen)
    - **email**: Valid email address
    - **password**: Password (min 8 chars, uppercase, lowercase, digit)
    - **first_name**: First name
    - **last_name**: Last name
    - **phone_number**: Optional phone number
    - **is_active**: Account active status (default: True)
    - **is_verified**: Email verification status (default: True)
    - **role_ids**: List of role IDs to assign (optional)
    """
    user_service = UserService(db)

    # Check if username already exists
    existing_user = await user_service.get_by_username(request.username)
    if existing_user:
        raise ConflictException(message="Username already exists")

    # Check if email already exists
    existing_email = await user_service.get_by_email(request.email)
    if existing_email:
        raise ConflictException(message="Email already exists")

    # Hash the password
    password_hash = hash_password(request.password)

    # Create the user
    new_user = User(
        username=request.username,
        email=request.email,
        password_hash=password_hash,
        first_name=request.first_name,
        last_name=request.last_name,
        phone_number=request.phone_number,
        is_active=request.is_active,
        is_verified=request.is_verified,
        two_factor_enabled=False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Assign roles if provided
    role_service = RoleService(db)
    if request.role_ids:
        for role_id in request.role_ids:
            try:
                await role_service.assign_role(
                    user_id=new_user.user_id,
                    role_id=role_id,
                    assigned_by=admin.user_id,
                )
            except Exception:
                # Skip invalid role IDs
                pass
    else:
        # Assign default user role if no roles specified
        default_role = await db.execute(
            select(Role).where(Role.role_code == "user")
        )
        default_role = default_role.scalar_one_or_none()
        if default_role:
            await role_service.assign_role(
                user_id=new_user.user_id,
                role_id=default_role.role_id,
                assigned_by=admin.user_id,
            )

    # Refresh to get roles
    await db.refresh(new_user)
    roles = user_service.get_user_roles(new_user)

    return success_response(
        data={
            "user_id": new_user.user_id,
            "username": new_user.username,
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "phone_number": new_user.phone_number,
            "is_active": new_user.is_active,
            "is_verified": new_user.is_verified,
            "two_factor_enabled": new_user.two_factor_enabled,
            "created_at": new_user.created_at,
            "last_login_at": new_user.last_login_at,
            "roles": roles,
        },
        message="User created successfully",
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

    # Use role codes for API consistency (role_code is used for assign/remove operations)
    roles = user_service.get_user_role_codes(user)

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
    summary="Deactivate user (DELETE method)",
    response_description="User deactivated",
)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Deactivate a user account (soft delete) using DELETE method.

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


@router.post(
    "/users/{user_id}/deactivate",
    summary="Deactivate user",
    response_description="User deactivated",
)
async def deactivate_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Deactivate a user account.

    This sets `is_active` to False. The user can be reactivated later.

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


@router.post(
    "/users/{user_id}/activate",
    summary="Activate user",
    response_description="User activated",
)
async def activate_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Activate a user account.

    This sets `is_active` to True.

    **Requires:** Admin role

    **Path Parameters:**
    - **user_id**: User ID
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    user.is_active = True
    await db.commit()

    return success_response(
        data={"user_id": user_id, "is_active": True},
        message="User activated successfully",
    )


@router.post(
    "/users/{user_id}/reset-password",
    summary="Reset user password",
    response_description="Password reset successfully",
)
async def reset_user_password(
    user_id: int,
    request: AdminPasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Reset a user's password (admin only).

    **Requires:** Admin role

    **Path Parameters:**
    - **user_id**: User ID

    **Request Body:**
    - **new_password**: New password (min 8 chars)
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    # Hash and update password
    user.password_hash = hash_password(request.new_password)
    await db.commit()

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_action(
        action_type=ActionType.UPDATE,
        user_id=admin.user_id,
        entity_type=EntityType.USER,
        entity_id=user_id,
        description=f"Admin reset password for user {user_id}",
    )

    return success_response(
        data={"user_id": user_id},
        message="Password reset successfully",
    )


@router.post(
    "/users/{user_id}/disable-2fa",
    summary="Force disable 2FA for user",
    response_description="2FA disabled successfully",
)
async def force_disable_2fa(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Force disable 2FA for a user (admin only).

    Use this when a user has lost access to their authenticator app.

    **Requires:** Admin role

    **Path Parameters:**
    - **user_id**: User ID
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    if not user.two_factor_enabled:
        raise ValidationException(message="2FA is not enabled for this user")

    # Disable 2FA
    user.two_factor_enabled = False
    user.two_factor_secret = None
    await db.commit()

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log_action(
        action_type=ActionType.UPDATE,
        user_id=admin.user_id,
        entity_type=EntityType.USER,
        entity_id=user_id,
        description=f"Admin disabled 2FA for user {user_id}",
    )

    return success_response(
        data={"user_id": user_id, "two_factor_enabled": False},
        message="Two-factor authentication disabled for user",
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
    - **role_code**: Role code to assign
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    role_service = RoleService(db)
    user_role = await role_service.assign_role_by_code(
        user_id=user_id,
        role_code=request.role_code,
        assigned_by=admin.user_id,
    )

    role = await role_service.get_role_by_code(request.role_code)

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
    "/users/{user_id}/roles/{role_code}",
    summary="Remove role from user",
    response_description="Role removed",
)
async def remove_role(
    user_id: int,
    role_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Remove a role from a user.

    **Requires:** Admin role

    **Path Parameters:**
    - **user_id**: User ID
    - **role_code**: Role code to remove

    **Note:** Users must have at least one role.
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise NotFoundException(message="User not found")

    role_service = RoleService(db)
    role = await role_service.get_role_by_code(role_code)

    if not role:
        raise NotFoundException(message="Role not found")

    # Prevent admin from removing their own admin role
    if user_id == admin.user_id and role_code == "admin":
        raise ValidationException(
            message="Cannot remove admin role from yourself"
        )

    await role_service.remove_role_by_code(user_id, role_code)

    return success_response(
        data={"user_id": user_id, "role_code": role_code},
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


# ═══════════════════════════════════════════════════════════
# ADMIN LOGIN HISTORY
# ═══════════════════════════════════════════════════════════


@router.get(
    "/login-history",
    summary="Get paginated login history for all users",
    response_description="Paginated login history",
)
async def get_admin_login_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    user_id: int | None = Query(default=None, description="Filter by user ID"),
    status: str | None = Query(default=None, description="Filter by status (success/failed)"),
) -> dict[str, Any]:
    """
    Get paginated login history for all users.

    **Requires:** Admin role

    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **user_id**: Filter by specific user (optional)
    - **status**: Filter by status - 'success' or 'failed' (optional)
    """
    # Build query
    query = select(AuditLog).where(
        AuditLog.action_type.in_([ActionType.LOGIN, ActionType.LOGIN_FAILED, ActionType.LOGOUT])
    )

    # Apply filters
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    if status == "success":
        query = query.where(AuditLog.action_type == ActionType.LOGIN)
    elif status == "failed":
        query = query.where(AuditLog.action_type == ActionType.LOGIN_FAILED)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    audit_service = AuditService(db)
    log_data = await audit_service.enrich_logs_with_usernames(list(logs))

    return paginated_response(
        data=log_data,
        page=page,
        per_page=page_size,
        total_items=total,
    )


# ═══════════════════════════════════════════════════════════
# SECURITY DASHBOARD
# ═══════════════════════════════════════════════════════════


@router.get(
    "/security/stats",
    summary="Get security statistics",
    response_description="Security dashboard statistics",
)
async def get_security_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Get security statistics for the dashboard.

    **Requires:** Admin role

    Returns statistics including:
    - Total users and active users
    - Users with 2FA enabled
    - Locked accounts count
    - Recent failed login attempts
    """
    user_service = UserService(db)
    audit_service = AuditService(db)

    # Get user counts
    total_users = await db.execute(select(func.count(User.user_id)))
    total_users = total_users.scalar() or 0

    active_users = await db.execute(
        select(func.count(User.user_id)).where(User.is_active == True)
    )
    active_users = active_users.scalar() or 0

    users_with_2fa = await db.execute(
        select(func.count(User.user_id)).where(User.two_factor_enabled == True)
    )
    users_with_2fa = users_with_2fa.scalar() or 0

    # Get locked accounts (locked_until > now)
    locked_accounts = await db.execute(
        select(func.count(User.user_id)).where(
            User.locked_until != None,
            User.locked_until > datetime.utcnow()
        )
    )
    locked_accounts = locked_accounts.scalar() or 0

    # Get failed logins in last 24 hours
    yesterday = datetime.utcnow() - timedelta(hours=24)
    failed_logins_24h = await db.execute(
        select(func.count(AuditLog.log_id)).where(
            AuditLog.action_type == ActionType.LOGIN_FAILED,
            AuditLog.created_at >= yesterday
        )
    )
    failed_logins_24h = failed_logins_24h.scalar() or 0

    # Get unverified users
    unverified_users = await db.execute(
        select(func.count(User.user_id)).where(User.is_verified == False)
    )
    unverified_users = unverified_users.scalar() or 0

    # Calculate inactive accounts (users who haven't logged in for 30 days or never logged in)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    inactive_accounts = await db.execute(
        select(func.count(User.user_id)).where(
            User.is_active == True,
            (User.last_login_at == None) | (User.last_login_at < thirty_days_ago)
        )
    )
    inactive_accounts = inactive_accounts.scalar() or 0

    # Suspicious activities: count of IPs with 5+ failed logins in last 24h
    # First, get IPs with >= 5 failed logins
    suspicious_ips_subquery = (
        select(AuditLog.ip_address)
        .where(
            AuditLog.action_type == ActionType.LOGIN_FAILED,
            AuditLog.created_at >= yesterday,
            AuditLog.ip_address != None
        )
        .group_by(AuditLog.ip_address)
        .having(func.count(AuditLog.log_id) >= 5)
    ).subquery()

    suspicious_result = await db.execute(
        select(func.count()).select_from(suspicious_ips_subquery)
    )
    suspicious_count = suspicious_result.scalar() or 0

    return success_response(
        data={
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "users_with_2fa": users_with_2fa,
            "users_without_2fa": active_users - users_with_2fa,
            "locked_accounts": locked_accounts,
            "failed_logins_24h": failed_logins_24h,
            "unverified_users": unverified_users,
            "two_factor_adoption_rate": round(users_with_2fa / active_users * 100, 1) if active_users > 0 else 0,
            "inactive_accounts": inactive_accounts,
            "suspicious_activities": suspicious_count,
        }
    )


@router.get(
    "/security/locked-accounts",
    summary="Get locked accounts",
    response_description="List of currently locked accounts",
)
async def get_locked_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Get list of currently locked user accounts.

    **Requires:** Admin role
    """
    result = await db.execute(
        select(User)
        .where(
            User.locked_until != None,
            User.locked_until > datetime.utcnow()
        )
        .order_by(User.locked_until.desc())
    )
    locked_users = result.scalars().all()

    accounts = []
    for user in locked_users:
        accounts.append({
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "locked_until": user.locked_until.isoformat() if user.locked_until else None,
            "failed_login_attempts": user.failed_login_attempts,
            "last_failed_login": user.last_failed_login.isoformat() if user.last_failed_login else None,
        })

    return success_response(
        data={
            "accounts": accounts,
            "count": len(accounts),
        }
    )


@router.get(
    "/security/failed-logins",
    summary="Get recent failed login attempts",
    response_description="List of recent failed login attempts",
)
async def get_failed_logins(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back"),
) -> dict[str, Any]:
    """
    Get recent failed login attempts.

    **Requires:** Admin role

    **Query Parameters:**
    - **hours**: Number of hours to look back (default: 24, max: 168/1 week)
    """
    since = datetime.utcnow() - timedelta(hours=hours)

    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.action_type == ActionType.LOGIN_FAILED,
            AuditLog.created_at >= since
        )
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    )
    failed_logins = result.scalars().all()

    audit_service = AuditService(db)
    logs = await audit_service.enrich_logs_with_usernames(list(failed_logins))

    return success_response(
        data={
            "logs": logs,
            "count": len(logs),
            "hours": hours,
        }
    )


@router.get(
    "/security/users-without-2fa",
    summary="Get users without 2FA",
    response_description="List of active users without 2FA enabled",
)
async def get_users_without_2fa(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin())],
) -> dict[str, Any]:
    """
    Get list of active users who haven't enabled two-factor authentication.

    **Requires:** Admin role
    """
    result = await db.execute(
        select(User)
        .where(
            User.is_active == True,
            User.two_factor_enabled == False
        )
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    user_list = []
    for user in users:
        user_list.append({
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        })

    return success_response(
        data={
            "users": user_list,
            "count": len(user_list),
        }
    )
