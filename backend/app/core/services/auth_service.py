"""
Authentication Service

Business logic for authentication operations.
"""

import secrets
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.models import User, UserSession
from app.core.services.user_service import UserService
from app.core.services.session_service import SessionService
from app.core.services.two_factor_service import TwoFactorService
from app.core.services.audit_service import AuditService
from app.shared.exceptions import (
    InvalidCredentialsException,
    AccountDisabledException,
    AccountLockedException,
    TokenInvalidException,
    TokenExpiredException,
    ValidationException,
    SessionRevokedException,
    TwoFactorInvalidException,
)
from app.shared.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token,
    TokenType,
)


class AuthService:
    """Service class for authentication operations."""

    # Account lockout configuration
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
        self.session_service = SessionService(db)
        self.two_factor_service = TwoFactorService(db)
        self.audit_service = AuditService(db)

    # ═══════════════════════════════════════════════════════════
    # REGISTRATION
    # ═══════════════════════════════════════════════════════════

    async def register(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone_number: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        """
        Register a new user.

        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
            first_name: First name
            last_name: Last name
            phone_number: Optional phone number
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit

        Returns:
            Created User object

        Raises:
            AlreadyExistsException: If username or email already exists
        """
        # Hash the password
        password_hash = hash_password(password)

        # Create user via user service
        user = await self.user_service.create(
            username=username,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
        )

        # Audit log registration
        await self.audit_service.log_registration(
            user_id=user.user_id,
            username=username,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return user

    # ═══════════════════════════════════════════════════════════
    # LOGIN
    # ═══════════════════════════════════════════════════════════

    async def authenticate(
        self,
        username_or_email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, bool]:
        """
        Authenticate user credentials.

        Args:
            username_or_email: Username or email
            password: Plain text password
            ip_address: Client IP address (for audit logging)
            user_agent: Client user agent (for audit logging)

        Returns:
            Tuple of (User, requires_2fa)

        Raises:
            InvalidCredentialsException: If credentials are invalid
            AccountDisabledException: If account is disabled
            AccountLockedException: If account is locked due to too many failed attempts
        """
        # Find user
        user = await self.user_service.get_by_username_or_email(username_or_email)

        if not user:
            # Use same error to prevent username enumeration
            raise InvalidCredentialsException()

        # Check if account is locked
        if user.is_locked:
            remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
            raise AccountLockedException(
                message=f"Account is locked due to too many failed attempts. Try again in {remaining} minute(s)."
            )

        # Verify password
        if not verify_password(password, user.password_hash):
            # Increment failed login attempts
            await self._record_failed_login(user, ip_address, user_agent)
            raise InvalidCredentialsException()

        # Check if account is active
        if not user.is_active:
            raise AccountDisabledException()

        # Successful authentication - reset failed attempts
        if user.failed_login_attempts > 0:
            await self._reset_failed_attempts(user)

        # Check if 2FA is required
        requires_2fa = user.two_factor_enabled

        return user, requires_2fa

    async def _record_failed_login(
        self,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Record a failed login attempt and potentially lock the account.

        Args:
            user: User who failed to authenticate
            ip_address: Client IP address
            user_agent: Client user agent
        """
        user.failed_login_attempts += 1

        # Check if we need to lock the account
        if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)

            # Log account lockout
            await self.audit_service.log_action(
                user_id=user.user_id,
                action_type="ACCOUNT_LOCKED",
                entity_type="USER",
                entity_id=str(user.user_id),
                description=f"Account locked after {user.failed_login_attempts} failed login attempts",
                ip_address=ip_address,
                user_agent=user_agent,
            )

        # Log failed login attempt
        await self.audit_service.log_login(
            user_id=user.user_id,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=f"Invalid password (attempt {user.failed_login_attempts}/{self.MAX_FAILED_ATTEMPTS})",
        )

        await self.db.commit()

    async def _reset_failed_attempts(self, user: User) -> None:
        """Reset failed login attempts after successful authentication."""
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.db.commit()

    async def login(
        self,
        username_or_email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """
        Complete login flow.

        Args:
            username_or_email: Username or email
            password: Plain text password
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            Dictionary with user info and tokens, or 2FA requirement

        Raises:
            InvalidCredentialsException: If credentials are invalid
            AccountDisabledException: If account is disabled
            AccountLockedException: If account is locked
        """
        user, requires_2fa = await self.authenticate(
            username_or_email, password, ip_address, user_agent
        )

        if requires_2fa:
            # Generate temporary token for 2FA verification
            temp_token = self._generate_temp_token(user)
            return {
                "requires_2fa": True,
                "temp_token": temp_token,
                "user_id": str(user.user_id),
            }

        # Generate tokens and complete login
        return await self._complete_login(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def _complete_login(
        self,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
        two_factor_method: str | None = None,
    ) -> dict:
        """
        Complete login by generating tokens, creating session, and updating last login.

        Args:
            user: Authenticated user
            ip_address: Client IP address
            user_agent: Client user agent string
            two_factor_method: 2FA method used ("totp" or "backup_code") if any

        Returns:
            Dictionary with user info, tokens, and session
        """
        # Update last login timestamp
        await self.user_service.update_last_login(user.user_id)

        # Get user roles
        roles = self.user_service.get_user_roles(user)

        # Generate tokens (with JTI for session tracking)
        tokens = self.create_tokens(user, roles)

        # Create session linked to refresh token
        session = await self.session_service.create_session(
            user_id=user.user_id,
            refresh_token_jti=tokens["jti"],
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Audit log successful login
        await self.audit_service.log_login(
            user_id=user.user_id,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # If 2FA was used, log that separately
        if two_factor_method:
            await self.audit_service.log_2fa_verify(
                user_id=user.user_id,
                method=two_factor_method,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return {
            "user": {
                "user_id": str(user.user_id),
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "roles": roles,
            },
            "tokens": {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": tokens["token_type"],
                "expires_in": tokens["expires_in"],
            },
            "session_id": session.session_id,
        }

    def _generate_temp_token(self, user: User) -> str:
        """
        Generate a temporary token for 2FA verification.

        This is a simple implementation - in production, you might want to
        store this in Redis with expiration.
        """
        # Create a short-lived token
        token_data = {
            "sub": str(user.user_id),
            "purpose": "2fa_verify",
        }
        return create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=5),  # 5 minute expiry
        )

    # ═══════════════════════════════════════════════════════════
    # TWO-FACTOR AUTHENTICATION
    # ═══════════════════════════════════════════════════════════

    async def verify_2fa_login(
        self,
        temp_token: str,
        code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """
        Complete login with 2FA TOTP code verification.

        Args:
            temp_token: Temporary token from initial login
            code: 6-digit TOTP code
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            Dictionary with user info, tokens, and session

        Raises:
            TokenInvalidException: If temp token is invalid or expired
            TwoFactorInvalidException: If TOTP code is invalid
        """
        # Verify temp token
        payload = verify_token(temp_token, TokenType.ACCESS)

        if payload is None:
            raise TokenInvalidException(message="Invalid or expired temporary token")

        # Check token purpose
        if payload.get("purpose") != "2fa_verify":
            raise TokenInvalidException(message="Invalid token purpose")

        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalidException(message="Invalid token payload")

        # Get user
        user = await self.user_service.get_by_id(int(user_id))
        if not user:
            raise TokenInvalidException(message="User not found")

        if not user.is_active:
            raise AccountDisabledException()

        # Verify TOTP code
        await self.two_factor_service.verify_code(user.user_id, code)

        # Complete login with 2FA method noted
        return await self._complete_login(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            two_factor_method="totp",
        )

    async def verify_2fa_login_backup(
        self,
        temp_token: str,
        backup_code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """
        Complete login with 2FA backup code verification.

        Args:
            temp_token: Temporary token from initial login
            backup_code: One-time backup code
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            Dictionary with user info, tokens, and session

        Raises:
            TokenInvalidException: If temp token is invalid or expired
            TwoFactorInvalidException: If backup code is invalid
        """
        # Verify temp token
        payload = verify_token(temp_token, TokenType.ACCESS)

        if payload is None:
            raise TokenInvalidException(message="Invalid or expired temporary token")

        # Check token purpose
        if payload.get("purpose") != "2fa_verify":
            raise TokenInvalidException(message="Invalid token purpose")

        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalidException(message="Invalid token payload")

        # Get user
        user = await self.user_service.get_by_id(int(user_id))
        if not user:
            raise TokenInvalidException(message="User not found")

        if not user.is_active:
            raise AccountDisabledException()

        # Verify backup code (this also consumes the code)
        await self.two_factor_service.verify_backup_code(user.user_id, backup_code)

        # Complete login with backup_code method noted
        return await self._complete_login(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            two_factor_method="backup_code",
        )

    # ═══════════════════════════════════════════════════════════
    # TOKEN MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    def create_tokens(self, user: User, roles: list[str]) -> dict:
        """
        Create access and refresh tokens for a user.

        Args:
            user: User object
            roles: List of role names

        Returns:
            Dictionary with tokens and JTI
        """
        # Generate unique JTI for session tracking
        jti = secrets.token_urlsafe(32)

        token_data = {
            "sub": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "roles": roles,
        }

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data={"sub": str(user.user_id), "jti": jti})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "jti": jti,
        }

    async def refresh_tokens(
        self,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            Dictionary with new tokens

        Raises:
            TokenInvalidException: If refresh token is invalid
            TokenExpiredException: If refresh token has expired
            SessionRevokedException: If session has been revoked
        """
        # Verify refresh token
        payload = verify_token(refresh_token, TokenType.REFRESH)

        if payload is None:
            raise TokenInvalidException(message="Invalid refresh token")

        # Get user and JTI
        user_id = payload.get("sub")
        jti = payload.get("jti")

        if not user_id:
            raise TokenInvalidException(message="Invalid token payload")

        # Validate session if JTI exists
        if jti:
            session = await self.session_service.validate_session(jti)
            if session is None:
                raise SessionRevokedException()

            # Update session activity
            await self.session_service.update_activity(session.session_id)

        user = await self.user_service.get_by_id(int(user_id))

        if not user:
            raise TokenInvalidException(message="User not found")

        if not user.is_active:
            raise AccountDisabledException()

        # Get roles and create new access token only (keep same refresh token)
        roles = self.user_service.get_user_roles(user)
        token_data = {
            "sub": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "roles": roles,
        }

        access_token = create_access_token(data=token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,  # Return same refresh token
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    # ═══════════════════════════════════════════════════════════
    # PASSWORD MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Change user password.

        Args:
            user_id: User ID (integer)
            current_password: Current password for verification
            new_password: New password
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit

        Raises:
            InvalidCredentialsException: If current password is wrong
            ValidationException: If new password same as current
        """
        user = await self.user_service.get_by_id(user_id)

        if not user:
            raise InvalidCredentialsException()

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsException(message="Current password is incorrect")

        # Check new password is different
        if verify_password(new_password, user.password_hash):
            raise ValidationException(
                message="New password must be different from current password"
            )

        # Update password
        new_hash = hash_password(new_password)
        await self.user_service.update_password(user_id, new_hash)

        # Audit log password change
        await self.audit_service.log_password_change(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # ═══════════════════════════════════════════════════════════
    # SESSION VALIDATION
    # ═══════════════════════════════════════════════════════════

    async def validate_token(self, token: str) -> dict | None:
        """
        Validate an access token and return user info.

        Args:
            token: JWT access token

        Returns:
            Dictionary with user info if valid, None otherwise
        """
        payload = verify_token(token, TokenType.ACCESS)

        if payload is None:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Verify user still exists and is active
        user = await self.user_service.get_by_id(int(user_id))

        if not user or not user.is_active:
            return None

        roles = self.user_service.get_user_roles(user)

        return {
            "valid": True,
            "user_id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "roles": roles,
        }

    # ═══════════════════════════════════════════════════════════
    # LOGOUT / SESSION MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    async def logout(
        self,
        refresh_token: str,
        user_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """
        Logout by revoking the session associated with the refresh token.

        Args:
            refresh_token: The refresh token to revoke
            user_id: User ID for audit logging
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit

        Returns:
            True if session was revoked, False otherwise
        """
        # Decode token to get JTI
        payload = decode_token(refresh_token)

        if payload is None:
            return False

        jti = payload.get("jti")
        if not jti:
            return False

        # Get session before revoking for audit
        session = await self.session_service.get_by_refresh_token(jti)
        session_id = session.session_id if session else None

        # Revoke the session
        result = await self.session_service.revoke_session_by_refresh_token(jti)

        # Audit log logout
        if result and user_id:
            await self.audit_service.log_logout(
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return result

    async def logout_all_sessions(
        self,
        user_id: int,
        except_current_token: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> int:
        """
        Logout all sessions for a user.

        Args:
            user_id: User ID
            except_current_token: Optional refresh token to keep active
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit

        Returns:
            Number of sessions revoked
        """
        except_session_id = None

        if except_current_token:
            payload = decode_token(except_current_token)
            if payload:
                jti = payload.get("jti")
                if jti:
                    session = await self.session_service.get_by_refresh_token(jti)
                    if session:
                        except_session_id = session.session_id

        count = await self.session_service.revoke_all_sessions(
            user_id=user_id,
            except_session_id=except_session_id,
        )

        # Audit log session revocation
        if count > 0:
            await self.audit_service.log_all_sessions_revoke(
                user_id=user_id,
                revoked_by=user_id,
                count=count,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return count

    async def get_user_sessions(self, user_id: int) -> list:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of UserSession objects
        """
        return await self.session_service.get_user_sessions(user_id)

    async def revoke_session(
        self,
        session_id: int,
        user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """
        Revoke a specific session.

        Args:
            session_id: Session ID to revoke
            user_id: User ID (for authorization check)
            ip_address: Client IP address for audit
            user_agent: Client user agent for audit

        Returns:
            True if session was revoked

        Raises:
            NotFoundException: If session not found
        """
        result = await self.session_service.revoke_session(session_id, user_id)

        # Audit log session revocation
        if result:
            await self.audit_service.log_session_revoke(
                user_id=user_id,
                session_id=session_id,
                revoked_by=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return result
