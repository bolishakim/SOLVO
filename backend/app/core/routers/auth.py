"""
Authentication Router

API endpoints for user authentication.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    PasswordChangeRequest,
    LogoutRequest,
    LogoutAllRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.core.schemas.session import (
    SessionResponse,
    SessionListResponse,
    SessionRevokeResponse,
    SessionRevokeAllResponse,
)
from app.core.schemas.two_factor import (
    TwoFactorVerifyRequest,
    TwoFactorDisableRequest,
    TwoFactorLoginRequest,
    BackupCodeVerifyRequest,
)
from app.core.schemas.user import UserWithRolesResponse
from app.core.services.auth_service import AuthService
from app.core.services.user_service import UserService
from app.core.services.two_factor_service import TwoFactorService
from app.core.services.password_reset_service import PasswordResetService
from app.shared.security import verify_password
from app.core.dependencies import (
    get_current_active_user,
    ActiveUser,
    ClientIP,
    UserAgent,
)
from app.core.models import User
from app.shared.responses import success_response


router = APIRouter()


# ═══════════════════════════════════════════════════════════
# REGISTRATION
# ═══════════════════════════════════════════════════════════


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    response_description="User created successfully",
)
async def register(
    request: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    client_ip: ClientIP,
    user_agent: UserAgent,
) -> dict[str, Any]:
    """
    Register a new user account.

    Creates a new user with the provided information and assigns
    the default 'Standard User' role.

    **Request Body:**
    - **username**: Unique username (3-50 chars, alphanumeric with underscore/hyphen)
    - **email**: Valid email address
    - **password**: Password (min 8 chars, must contain uppercase, lowercase, digit)
    - **first_name**: First name
    - **last_name**: Last name
    - **phone_number**: Optional phone number

    **Returns:**
    - User information with assigned roles

    **Errors:**
    - 400: Validation error (invalid input format)
    - 409: Username or email already exists
    """
    auth_service = AuthService(db)

    user = await auth_service.register(
        username=request.username,
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        phone_number=request.phone_number,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    user_service = UserService(db)
    roles = user_service.get_user_roles(user)

    return success_response(
        data={
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": roles,
        },
        message="Registration successful",
    )


# ═══════════════════════════════════════════════════════════
# LOGIN / LOGOUT
# ═══════════════════════════════════════════════════════════


@router.post(
    "/login",
    summary="User login",
    response_description="Login successful with tokens",
)
async def login(
    request: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    client_ip: ClientIP,
    user_agent: UserAgent,
) -> dict[str, Any]:
    """
    Authenticate user and obtain access tokens.

    **Request Body:**
    - **username_or_email**: Username or email address
    - **password**: User password

    **Returns:**
    - If 2FA is not enabled: User info, access/refresh tokens, and session ID
    - If 2FA is enabled: Temporary token for 2FA verification

    **Response (without 2FA):**
    ```json
    {
        "success": true,
        "message": "Login successful",
        "data": {
            "user": {
                "user_id": "...",
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "roles": ["Standard User"]
            },
            "tokens": {
                "access_token": "eyJ...",
                "refresh_token": "eyJ...",
                "token_type": "bearer",
                "expires_in": 3600
            },
            "session_id": 1
        }
    }
    ```

    **Response (with 2FA):**
    ```json
    {
        "success": true,
        "message": "Two-factor authentication required",
        "data": {
            "requires_2fa": true,
            "temp_token": "eyJ..."
        }
    }
    ```

    **Errors:**
    - 401: Invalid credentials
    - 403: Account disabled
    """
    auth_service = AuthService(db)

    result = await auth_service.login(
        username_or_email=request.username_or_email,
        password=request.password,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    if result.get("requires_2fa"):
        return success_response(
            data=result,
            message="Two-factor authentication required",
        )

    return success_response(
        data=result,
        message="Login successful",
    )


@router.post(
    "/logout",
    summary="User logout",
    response_description="Logout successful",
)
async def logout(
    request: LogoutRequest,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    client_ip: ClientIP,
    user_agent: UserAgent,
) -> dict[str, Any]:
    """
    Logout the current user by revoking their session.

    This endpoint invalidates the session associated with the provided
    refresh token. The client should discard the access and refresh tokens.

    **Requires:** Valid access token

    **Request Body:**
    - **refresh_token**: The refresh token to invalidate

    **Returns:**
    - Success message
    """
    auth_service = AuthService(db)

    await auth_service.logout(
        refresh_token=request.refresh_token,
        user_id=current_user.user_id,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return success_response(
        data={"user_id": str(current_user.user_id)},
        message="Logout successful",
    )


# ═══════════════════════════════════════════════════════════
# TOKEN MANAGEMENT
# ═══════════════════════════════════════════════════════════


@router.post(
    "/refresh-token",
    summary="Refresh access token",
    response_description="New tokens generated",
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Refresh the access token using a valid refresh token.

    Use this endpoint when the access token has expired but the
    refresh token is still valid.

    **Request Body:**
    - **refresh_token**: Valid refresh token

    **Returns:**
    - New access and refresh tokens

    **Errors:**
    - 401: Invalid or expired refresh token
    - 403: Account disabled
    """
    auth_service = AuthService(db)

    tokens = await auth_service.refresh_tokens(request.refresh_token)

    return success_response(
        data={"tokens": tokens},
        message="Token refreshed successfully",
    )


@router.get(
    "/session/validate",
    summary="Validate current session",
    response_description="Session validation result",
)
async def validate_session(
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Validate the current session/token.

    Use this endpoint to check if the current access token is valid
    and get the current user's information.

    **Requires:** Valid access token

    **Returns:**
    - Session validity status
    - Current user information
    - User roles
    """
    user_service = UserService(db)
    roles = user_service.get_user_roles(current_user)

    return success_response(
        data={
            "valid": True,
            "user_id": str(current_user.user_id),
            "username": current_user.username,
            "email": current_user.email,
            "roles": roles,
        },
    )


# ═══════════════════════════════════════════════════════════
# PASSWORD MANAGEMENT
# ═══════════════════════════════════════════════════════════


@router.post(
    "/change-password",
    summary="Change password",
    response_description="Password changed successfully",
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    client_ip: ClientIP,
    user_agent: UserAgent,
) -> dict[str, Any]:
    """
    Change the current user's password.

    **Requires:** Valid access token

    **Request Body:**
    - **current_password**: Current password for verification
    - **new_password**: New password (must meet strength requirements)

    **Returns:**
    - Success message

    **Errors:**
    - 401: Current password is incorrect
    - 400: New password same as current or doesn't meet requirements
    """
    auth_service = AuthService(db)

    await auth_service.change_password(
        user_id=current_user.user_id,
        current_password=request.current_password,
        new_password=request.new_password,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return success_response(
        data={"user_id": str(current_user.user_id)},
        message="Password changed successfully",
    )


@router.post(
    "/forgot-password",
    summary="Request password reset",
    response_description="Password reset email sent (if account exists)",
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    client_ip: ClientIP,
    user_agent: UserAgent,
) -> dict[str, Any]:
    """
    Request a password reset email.

    If the email is associated with an account, a reset token will be generated.
    For security, the response is the same whether the email exists or not.

    **Request Body:**
    - **email**: Email address associated with the account

    **Returns:**
    - Success message (always, to prevent email enumeration)

    **Note:** In a production environment, this would send an email with
    the reset link. For development, the token is returned in the response.
    """
    reset_service = PasswordResetService(db)

    token = await reset_service.create_reset_token(
        email=request.email,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    # In production, send email instead of returning token
    # For development, we return the token for testing
    response_data = {
        "message": "If an account exists with this email, a reset link will be sent.",
    }

    # Include token in development for testing
    # TODO: Remove in production and send email instead
    if token:
        response_data["_dev_token"] = token

    return success_response(
        data=response_data,
        message="Password reset instructions sent if account exists",
    )


@router.post(
    "/reset-password",
    summary="Reset password with token",
    response_description="Password reset successful",
)
async def reset_password(
    request: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    client_ip: ClientIP,
    user_agent: UserAgent,
) -> dict[str, Any]:
    """
    Reset password using a reset token.

    The token is obtained from the password reset email.

    **Request Body:**
    - **token**: Password reset token
    - **new_password**: New password (must meet strength requirements)

    **Returns:**
    - Success message

    **Errors:**
    - 400: Invalid or expired token
    - 400: Password doesn't meet requirements
    """
    reset_service = PasswordResetService(db)

    await reset_service.reset_password(
        token=request.token,
        new_password=request.new_password,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return success_response(
        data={},
        message="Password reset successful. You can now log in with your new password.",
    )


# ═══════════════════════════════════════════════════════════
# CURRENT USER
# ═══════════════════════════════════════════════════════════


@router.get(
    "/me",
    summary="Get current user",
    response_description="Current user information",
)
async def get_me(
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Get the current authenticated user's profile.

    **Requires:** Valid access token

    **Returns:**
    - Complete user profile information
    - Assigned roles
    """
    user_service = UserService(db)
    roles = user_service.get_user_roles(current_user)

    return success_response(
        data={
            "user_id": str(current_user.user_id),
            "username": current_user.username,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone_number": current_user.phone_number,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "two_factor_enabled": current_user.two_factor_enabled,
            "created_at": current_user.created_at.isoformat(),
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
            "roles": roles,
        },
    )


@router.put(
    "/me",
    summary="Update current user profile",
    response_description="Profile updated successfully",
)
async def update_me(
    first_name: str | None = None,
    last_name: str | None = None,
    phone_number: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update the current user's profile.

    **Requires:** Valid access token

    **Query Parameters:**
    - **first_name**: New first name (optional)
    - **last_name**: New last name (optional)
    - **phone_number**: New phone number (optional)

    **Returns:**
    - Updated user profile
    """
    user_service = UserService(db)

    updated_user = await user_service.update(
        user_id=current_user.user_id,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
    )

    roles = user_service.get_user_roles(updated_user)

    return success_response(
        data={
            "user_id": str(updated_user.user_id),
            "username": updated_user.username,
            "email": updated_user.email,
            "first_name": updated_user.first_name,
            "last_name": updated_user.last_name,
            "phone_number": updated_user.phone_number,
            "roles": roles,
        },
        message="Profile updated successfully",
    )


# ═══════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════


@router.get(
    "/sessions",
    summary="List user sessions",
    response_description="List of active sessions",
)
async def list_sessions(
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Get all active sessions for the current user.

    **Requires:** Valid access token

    **Returns:**
    - List of session objects with IP, user agent, and timestamps
    """
    auth_service = AuthService(db)

    sessions = await auth_service.get_user_sessions(current_user.user_id)

    session_list = [
        {
            "session_id": session.session_id,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
        }
        for session in sessions
    ]

    return success_response(
        data={"sessions": session_list, "count": len(session_list)},
    )


@router.delete(
    "/sessions/{session_id}",
    summary="Revoke a session",
    response_description="Session revoked",
)
async def revoke_session(
    session_id: int,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    client_ip: ClientIP,
    user_agent: UserAgent,
) -> dict[str, Any]:
    """
    Revoke a specific session.

    **Requires:** Valid access token

    **Path Parameters:**
    - **session_id**: ID of the session to revoke

    **Returns:**
    - Success message

    **Errors:**
    - 404: Session not found
    """
    auth_service = AuthService(db)

    await auth_service.revoke_session(
        session_id=session_id,
        user_id=current_user.user_id,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return success_response(
        data={"session_id": session_id},
        message="Session revoked successfully",
    )


@router.post(
    "/sessions/revoke-all",
    summary="Revoke all sessions",
    response_description="All sessions revoked",
)
async def revoke_all_sessions(
    request: LogoutAllRequest,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    client_ip: ClientIP,
    user_agent: UserAgent,
) -> dict[str, Any]:
    """
    Revoke all sessions for the current user.

    Optionally keep the current session active by providing
    the current refresh token.

    **Requires:** Valid access token

    **Request Body:**
    - **keep_current**: Whether to keep the current session active
    - **current_refresh_token**: Current refresh token (required if keep_current is True)

    **Returns:**
    - Number of sessions revoked
    """
    auth_service = AuthService(db)

    current_token = None
    if request.keep_current and request.current_refresh_token:
        current_token = request.current_refresh_token

    revoked_count = await auth_service.logout_all_sessions(
        user_id=current_user.user_id,
        except_current_token=current_token,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return success_response(
        data={"revoked_count": revoked_count},
        message=f"Revoked {revoked_count} session(s)",
    )


# ═══════════════════════════════════════════════════════════
# TWO-FACTOR AUTHENTICATION
# ═══════════════════════════════════════════════════════════


@router.post(
    "/2fa/setup",
    summary="Setup two-factor authentication",
    response_description="2FA setup initiated",
)
async def setup_2fa(
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Initiate two-factor authentication setup.

    Generates a new secret and returns a QR code URI for scanning
    with an authenticator app (Google Authenticator, Authy, etc.).

    **Requires:** Valid access token

    **Returns:**
    - Secret key (for manual entry)
    - QR code URI (for scanning)
    - Manual entry key

    **Note:** 2FA is not enabled until verified with `/2fa/verify`
    """
    two_factor_service = TwoFactorService(db)

    result = await two_factor_service.initiate_setup(current_user)

    return success_response(
        data=result,
        message="Scan the QR code with your authenticator app",
    )


@router.post(
    "/2fa/verify",
    summary="Verify and enable 2FA",
    response_description="2FA enabled",
)
async def verify_2fa(
    request: TwoFactorVerifyRequest,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Verify the TOTP code and enable two-factor authentication.

    After calling `/2fa/setup`, use this endpoint to verify the
    code from your authenticator app and enable 2FA.

    **Requires:** Valid access token

    **Request Body:**
    - **code**: 6-digit code from authenticator app

    **Returns:**
    - Enabled status
    - Backup codes (save these securely!)

    **Important:** Save the backup codes in a secure location.
    They can be used if you lose access to your authenticator app.
    """
    two_factor_service = TwoFactorService(db)

    result = await two_factor_service.verify_and_enable(current_user, request.code)

    return success_response(
        data=result,
        message="Two-factor authentication enabled. Save your backup codes!",
    )


@router.post(
    "/2fa/disable",
    summary="Disable two-factor authentication",
    response_description="2FA disabled",
)
async def disable_2fa(
    request: TwoFactorDisableRequest,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Disable two-factor authentication.

    Requires both the current TOTP code and password for security.

    **Requires:** Valid access token

    **Request Body:**
    - **code**: 6-digit code from authenticator app
    - **password**: Current password for verification

    **Returns:**
    - Success message
    """
    # Verify password first
    if not verify_password(request.password, current_user.password_hash):
        from app.shared.exceptions import InvalidCredentialsException
        raise InvalidCredentialsException(message="Invalid password")

    two_factor_service = TwoFactorService(db)

    await two_factor_service.disable(
        user=current_user,
        code=request.code,
        password_verified=True,
    )

    return success_response(
        data={},
        message="Two-factor authentication disabled",
    )


@router.get(
    "/2fa/status",
    summary="Get 2FA status",
    response_description="2FA status",
)
async def get_2fa_status(
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Get the current two-factor authentication status.

    **Requires:** Valid access token

    **Returns:**
    - Enabled status
    - Verified status
    - Number of backup codes remaining
    - Enabled timestamp
    - Last used timestamp
    """
    two_factor_service = TwoFactorService(db)

    status = await two_factor_service.get_status(current_user.user_id)

    return success_response(data=status)


@router.post(
    "/2fa/backup-codes/regenerate",
    summary="Regenerate backup codes",
    response_description="New backup codes",
)
async def regenerate_backup_codes(
    request: TwoFactorVerifyRequest,
    current_user: ActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """
    Regenerate backup codes.

    Generates new backup codes and invalidates all existing ones.
    Requires current TOTP code for verification.

    **Requires:** Valid access token

    **Request Body:**
    - **code**: 6-digit code from authenticator app

    **Returns:**
    - New backup codes

    **Important:** Save the new backup codes. Old codes will no longer work.
    """
    two_factor_service = TwoFactorService(db)

    backup_codes = await two_factor_service.regenerate_backup_codes(
        user=current_user,
        code=request.code,
    )

    return success_response(
        data={"backup_codes": backup_codes},
        message="New backup codes generated. Save them securely!",
    )


@router.post(
    "/login/2fa",
    summary="Complete login with 2FA",
    response_description="Login completed",
)
async def login_2fa(
    request: TwoFactorLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    client_ip: ClientIP,
    user_agent: UserAgent,
) -> dict[str, Any]:
    """
    Complete login with two-factor authentication.

    After initial login returns `requires_2fa: true`, use this endpoint
    with the temporary token and TOTP code to complete login.

    **Request Body:**
    - **temp_token**: Temporary token from initial login
    - **code**: 6-digit code from authenticator app

    **Returns:**
    - User info
    - Access and refresh tokens
    - Session ID

    **Errors:**
    - 401: Invalid temporary token or TOTP code
    """
    auth_service = AuthService(db)

    result = await auth_service.verify_2fa_login(
        temp_token=request.temp_token,
        code=request.code,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return success_response(
        data=result,
        message="Login successful",
    )


@router.post(
    "/login/backup-code",
    summary="Complete login with backup code",
    response_description="Login completed",
)
async def login_backup_code(
    request: BackupCodeVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    client_ip: ClientIP,
    user_agent: UserAgent,
) -> dict[str, Any]:
    """
    Complete login using a backup code.

    Use this if you've lost access to your authenticator app.
    Each backup code can only be used once.

    **Request Body:**
    - **temp_token**: Temporary token from initial login
    - **backup_code**: One-time backup code (format: XXXX-XXXX)

    **Returns:**
    - User info
    - Access and refresh tokens
    - Session ID

    **Errors:**
    - 401: Invalid temporary token or backup code
    """
    auth_service = AuthService(db)

    result = await auth_service.verify_2fa_login_backup(
        temp_token=request.temp_token,
        backup_code=request.backup_code,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return success_response(
        data=result,
        message="Login successful",
    )
