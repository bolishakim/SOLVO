"""
Password Reset Service

Business logic for password reset functionality.
"""

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.models import PasswordResetToken, User
from app.core.services.audit_service import AuditService
from app.shared.exceptions import NotFoundException, ValidationException
from app.shared.security import hash_password


class PasswordResetService:
    """Service class for password reset operations."""

    # Token expiration time in minutes
    TOKEN_EXPIRY_MINUTES = 30
    # Maximum active tokens per user
    MAX_ACTIVE_TOKENS = 3

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit_service = AuditService(db)

    async def create_reset_token(
        self,
        email: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str | None:
        """
        Create a password reset token for a user.

        Always returns success message to prevent email enumeration.

        Args:
            email: User's email address
            ip_address: Request IP address
            user_agent: Request user agent

        Returns:
            Reset token if user exists, None otherwise
        """
        # Find user by email
        user = await self._get_user_by_email(email)

        if not user:
            # Don't reveal that user doesn't exist
            return None

        if not user.is_active:
            # Don't reveal that user is inactive
            return None

        # Clean up old tokens for this user
        await self._cleanup_old_tokens(user.user_id)

        # Generate secure token
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(minutes=self.TOKEN_EXPIRY_MINUTES)

        # Create token record
        reset_token = PasswordResetToken(
            user_id=user.user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(reset_token)

        # Log the action
        await self.audit_service.log_action(
            user_id=user.user_id,
            action_type="PASSWORD_RESET_REQUESTED",
            entity_type="PASSWORD_RESET",
            description="Password reset requested",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self.db.commit()

        return raw_token

    async def validate_token(self, token: str) -> PasswordResetToken:
        """
        Validate a password reset token.

        Args:
            token: Raw reset token

        Returns:
            PasswordResetToken if valid

        Raises:
            ValidationException: If token is invalid or expired
        """
        token_hash = self._hash_token(token)

        query = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
        result = await self.db.execute(query)
        reset_token = result.scalar_one_or_none()

        if not reset_token:
            raise ValidationException(message="Invalid or expired reset token")

        if reset_token.is_used:
            raise ValidationException(message="Reset token has already been used")

        if reset_token.is_expired:
            raise ValidationException(message="Reset token has expired")

        return reset_token

    async def reset_password(
        self,
        token: str,
        new_password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """
        Reset a user's password using a reset token.

        Args:
            token: Raw reset token
            new_password: New password
            ip_address: Request IP address
            user_agent: Request user agent

        Returns:
            True if password was reset successfully

        Raises:
            ValidationException: If token is invalid
        """
        # Validate the token
        reset_token = await self.validate_token(token)

        # Get the user
        user = reset_token.user

        if not user or not user.is_active:
            raise ValidationException(message="Invalid or expired reset token")

        # Update password
        user.password_hash = hash_password(new_password)

        # Mark token as used
        reset_token.is_used = True
        reset_token.used_at = datetime.utcnow()

        # Clear any account lockout
        user.failed_login_attempts = 0
        user.locked_until = None

        # Invalidate all other reset tokens for this user
        await self._invalidate_user_tokens(user.user_id, exclude_token_id=reset_token.token_id)

        # Log the action
        await self.audit_service.log_action(
            user_id=user.user_id,
            action_type="PASSWORD_RESET_COMPLETED",
            entity_type="PASSWORD_RESET",
            description="Password reset completed",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self.db.commit()

        return True

    async def _get_user_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        query = select(User).where(User.email == email.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _cleanup_old_tokens(self, user_id: int) -> None:
        """
        Clean up old/expired tokens for a user.

        Keeps only MAX_ACTIVE_TOKENS most recent valid tokens.
        """
        # Get all tokens for user ordered by creation time
        query = (
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id)
            .order_by(PasswordResetToken.created_at.desc())
        )
        result = await self.db.execute(query)
        tokens = result.scalars().all()

        now = datetime.utcnow()
        valid_count = 0

        for token in tokens:
            # Delete expired or used tokens
            if token.is_expired or token.is_used:
                await self.db.delete(token)
            elif valid_count >= self.MAX_ACTIVE_TOKENS - 1:
                # Keep only MAX_ACTIVE_TOKENS - 1 (leaving room for new one)
                await self.db.delete(token)
            else:
                valid_count += 1

    async def _invalidate_user_tokens(
        self,
        user_id: int,
        exclude_token_id: int | None = None,
    ) -> None:
        """Invalidate all tokens for a user except the specified one."""
        query = select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.is_used == False,
        )
        if exclude_token_id:
            query = query.where(PasswordResetToken.token_id != exclude_token_id)

        result = await self.db.execute(query)
        tokens = result.scalars().all()

        for token in tokens:
            token.is_used = True
            token.used_at = datetime.utcnow()

    def _hash_token(self, token: str) -> str:
        """Hash a token using SHA-256."""
        return hashlib.sha256(token.encode()).hexdigest()
