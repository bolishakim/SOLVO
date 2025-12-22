"""
Core Dependencies

FastAPI dependencies for authentication and authorization.
"""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.models import User
from app.core.services.user_service import UserService
from app.shared.exceptions import (
    UnauthorizedException,
    ForbiddenException,
    AccountDisabledException,
    TokenInvalidException,
    TokenExpiredException,
)
from app.shared.security import (
    extract_token_from_header,
    verify_token,
    TokenType,
)


# ═══════════════════════════════════════════════════════════
# TOKEN EXTRACTION
# ═══════════════════════════════════════════════════════════


async def get_token_from_header(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """
    Extract and validate bearer token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        JWT token string

    Raises:
        UnauthorizedException: If no token provided
    """
    if not authorization:
        raise UnauthorizedException(message="Authorization header required")

    token = extract_token_from_header(authorization)

    if not token:
        raise UnauthorizedException(message="Invalid authorization header format")

    return token


# ═══════════════════════════════════════════════════════════
# CURRENT USER DEPENDENCIES
# ═══════════════════════════════════════════════════════════


async def get_current_user(
    token: Annotated[str, Depends(get_token_from_header)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        token: JWT access token
        db: Database session

    Returns:
        Current User object

    Raises:
        TokenInvalidException: If token is invalid
        TokenExpiredException: If token has expired
        UnauthorizedException: If user not found
    """
    # Verify token
    payload = verify_token(token, TokenType.ACCESS)

    if payload is None:
        raise TokenInvalidException()

    # Get user ID from token
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise TokenInvalidException(message="Invalid token payload")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise TokenInvalidException(message="Invalid user ID in token")

    # Get user from database
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise UnauthorizedException(message="User not found")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get the current authenticated user and verify they are active.

    Args:
        current_user: Current user from token

    Returns:
        Current active User object

    Raises:
        AccountDisabledException: If account is disabled
    """
    if not current_user.is_active:
        raise AccountDisabledException()

    return current_user


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]


# ═══════════════════════════════════════════════════════════
# ROLE-BASED ACCESS CONTROL
# ═══════════════════════════════════════════════════════════


def require_role(role_code: str):
    """
    Dependency factory that requires a specific role.

    Args:
        role_code: Role code to require (e.g., "admin", "standard_user")

    Returns:
        Dependency function that validates the role

    Example:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role("admin"))):
            ...
    """

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> User:
        user_service = UserService(db)

        if not user_service.has_role(current_user, role_code):
            raise ForbiddenException(
                message=f"Role '{role_code}' required for this action"
            )

        return current_user

    return role_checker


def require_any_role(*role_codes: str):
    """
    Dependency factory that requires any of the specified roles.

    Args:
        role_codes: Role codes, any of which satisfies the requirement

    Returns:
        Dependency function that validates the roles

    Example:
        @router.get("/staff-only")
        async def staff_endpoint(user: User = Depends(require_any_role("admin", "standard_user"))):
            ...
    """

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> User:
        user_service = UserService(db)
        user_roles = user_service.get_user_role_codes(current_user)

        if not any(role in user_roles for role in role_codes):
            raise ForbiddenException(
                message=f"One of roles {role_codes} required for this action"
            )

        return current_user

    return role_checker


def require_admin():
    """
    Shortcut dependency for requiring admin role.

    Returns:
        Dependency function that validates admin role

    Example:
        @router.delete("/users/{user_id}")
        async def delete_user(user: User = Depends(require_admin())):
            ...
    """
    return require_role("admin")


# ═══════════════════════════════════════════════════════════
# OPTIONAL AUTHENTICATION
# ═══════════════════════════════════════════════════════════


async def get_optional_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> User | None:
    """
    Optionally get the current user if authenticated.

    This dependency does not raise exceptions if no token is provided.
    Useful for endpoints that have different behavior for authenticated
    vs unauthenticated users.

    Args:
        authorization: Authorization header value (optional)
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not authorization:
        return None

    token = extract_token_from_header(authorization)
    if not token:
        return None

    payload = verify_token(token, TokenType.ACCESS)
    if payload is None:
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_id = int(user_id_str)
    except ValueError:
        return None

    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if user and user.is_active:
        return user

    return None


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


# ═══════════════════════════════════════════════════════════
# REQUEST INFO HELPERS
# ═══════════════════════════════════════════════════════════


async def get_client_ip(
    x_forwarded_for: Annotated[str | None, Header()] = None,
    x_real_ip: Annotated[str | None, Header()] = None,
) -> str | None:
    """
    Get client IP address from headers.

    Handles common proxy headers.

    Args:
        x_forwarded_for: X-Forwarded-For header
        x_real_ip: X-Real-IP header

    Returns:
        Client IP address or None
    """
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        return x_forwarded_for.split(",")[0].strip()
    if x_real_ip:
        return x_real_ip
    return None


async def get_user_agent(
    user_agent: Annotated[str | None, Header()] = None,
) -> str | None:
    """
    Get user agent from header.

    Args:
        user_agent: User-Agent header

    Returns:
        User agent string or None
    """
    return user_agent


ClientIP = Annotated[str | None, Depends(get_client_ip)]
UserAgent = Annotated[str | None, Depends(get_user_agent)]
