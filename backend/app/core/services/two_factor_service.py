"""
Two-Factor Authentication Service

Business logic for TOTP-based two-factor authentication.
"""

import secrets
from datetime import datetime

import pyotp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.models import TwoFactorAuth, User
from app.shared.exceptions import (
    TwoFactorInvalidException,
    TwoFactorRequiredException,
    ValidationException,
    NotFoundException,
)


class TwoFactorService:
    """Service class for two-factor authentication operations."""

    # Number of backup codes to generate
    BACKUP_CODE_COUNT = 10
    # Backup code format: XXXX-XXXX
    BACKUP_CODE_LENGTH = 8

    def __init__(self, db: AsyncSession):
        self.db = db

    # ═══════════════════════════════════════════════════════════
    # SETUP OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def initiate_setup(self, user: User) -> dict:
        """
        Initiate 2FA setup by generating a new secret.

        If user already has 2FA enabled, this will create a new pending
        secret that must be verified before replacing the old one.

        Args:
            user: User object

        Returns:
            Dictionary with secret and provisioning URI
        """
        # Check if already has verified 2FA
        existing = await self._get_two_factor(user.user_id)

        if existing and existing.is_enabled and existing.is_verified:
            raise ValidationException(
                message="Two-factor authentication is already enabled. Disable it first to set up again."
            )

        # Generate new secret
        secret = pyotp.random_base32()

        # Create or update 2FA record
        if existing:
            existing.secret_key = secret
            existing.is_enabled = False
            existing.is_verified = False
            existing.backup_codes = None
        else:
            two_factor = TwoFactorAuth(
                user_id=user.user_id,
                secret_key=secret,
                is_enabled=False,
                is_verified=False,
            )
            self.db.add(two_factor)

        await self.db.commit()

        # Generate provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.username,
            issuer_name=settings.APP_NAME,
        )

        return {
            "secret": secret,
            "qr_code_uri": provisioning_uri,
            "manual_entry_key": secret,
        }

    async def verify_and_enable(self, user: User, code: str) -> dict:
        """
        Verify the TOTP code and enable 2FA.

        Args:
            user: User object
            code: 6-digit TOTP code

        Returns:
            Dictionary with enabled status and backup codes

        Raises:
            TwoFactorInvalidException: If code is invalid
            ValidationException: If 2FA not set up
        """
        two_factor = await self._get_two_factor(user.user_id)

        if not two_factor:
            raise ValidationException(
                message="Two-factor authentication not set up. Call setup endpoint first."
            )

        if two_factor.is_enabled and two_factor.is_verified:
            raise ValidationException(
                message="Two-factor authentication is already enabled."
            )

        # Verify the code
        if not self._verify_totp(two_factor.secret_key, code):
            raise TwoFactorInvalidException()

        # Generate backup codes
        backup_codes = self._generate_backup_codes()

        # Enable 2FA
        two_factor.is_enabled = True
        two_factor.is_verified = True
        two_factor.enabled_at = datetime.utcnow()
        two_factor.backup_codes = ",".join(backup_codes)

        # Update user flag
        user.two_factor_enabled = True

        await self.db.commit()

        return {
            "enabled": True,
            "backup_codes": backup_codes,
        }

    async def disable(
        self,
        user: User,
        code: str,
        password_verified: bool = False,
    ) -> bool:
        """
        Disable 2FA for a user.

        Args:
            user: User object
            code: 6-digit TOTP code for verification
            password_verified: Whether password was already verified

        Returns:
            True if disabled successfully

        Raises:
            TwoFactorInvalidException: If code is invalid
            ValidationException: If 2FA not enabled
        """
        two_factor = await self._get_two_factor(user.user_id)

        if not two_factor or not two_factor.is_enabled:
            raise ValidationException(
                message="Two-factor authentication is not enabled."
            )

        # Verify the code
        if not self._verify_totp(two_factor.secret_key, code):
            raise TwoFactorInvalidException()

        # Disable 2FA
        two_factor.is_enabled = False
        two_factor.is_verified = False
        two_factor.backup_codes = None

        # Update user flag
        user.two_factor_enabled = False

        await self.db.commit()

        return True

    # ═══════════════════════════════════════════════════════════
    # VERIFICATION OPERATIONS
    # ═══════════════════════════════════════════════════════════

    async def verify_code(self, user_id: int, code: str) -> bool:
        """
        Verify a TOTP code for a user.

        Args:
            user_id: User ID
            code: 6-digit TOTP code

        Returns:
            True if code is valid

        Raises:
            TwoFactorInvalidException: If code is invalid
            ValidationException: If 2FA not enabled
        """
        two_factor = await self._get_two_factor(user_id)

        if not two_factor or not two_factor.is_enabled:
            raise ValidationException(
                message="Two-factor authentication is not enabled."
            )

        if not self._verify_totp(two_factor.secret_key, code):
            raise TwoFactorInvalidException()

        # Update last used timestamp
        two_factor.last_used_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def verify_backup_code(self, user_id: int, backup_code: str) -> bool:
        """
        Verify and consume a backup code.

        Args:
            user_id: User ID
            backup_code: Backup code (with or without hyphen)

        Returns:
            True if code is valid and consumed

        Raises:
            TwoFactorInvalidException: If code is invalid
            ValidationException: If 2FA not enabled or no backup codes
        """
        two_factor = await self._get_two_factor(user_id)

        if not two_factor or not two_factor.is_enabled:
            raise ValidationException(
                message="Two-factor authentication is not enabled."
            )

        if not two_factor.backup_codes:
            raise TwoFactorInvalidException(
                message="No backup codes available. Contact administrator."
            )

        # Normalize the backup code (remove hyphens)
        normalized_code = backup_code.replace("-", "").upper()

        # Get current backup codes
        current_codes = two_factor.backup_codes.split(",")
        normalized_codes = [c.replace("-", "").upper() for c in current_codes]

        if normalized_code not in normalized_codes:
            raise TwoFactorInvalidException(message="Invalid backup code")

        # Remove the used code
        idx = normalized_codes.index(normalized_code)
        current_codes.pop(idx)

        # Update backup codes
        two_factor.backup_codes = ",".join(current_codes) if current_codes else None
        two_factor.last_used_at = datetime.utcnow()

        await self.db.commit()

        return True

    # ═══════════════════════════════════════════════════════════
    # STATUS & MANAGEMENT
    # ═══════════════════════════════════════════════════════════

    async def get_status(self, user_id: int) -> dict:
        """
        Get 2FA status for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with 2FA status information
        """
        two_factor = await self._get_two_factor(user_id)

        if not two_factor:
            return {
                "enabled": False,
                "verified": False,
                "backup_codes_remaining": 0,
                "enabled_at": None,
                "last_used_at": None,
            }

        backup_count = 0
        if two_factor.backup_codes:
            backup_count = len(two_factor.backup_codes.split(","))

        return {
            "enabled": two_factor.is_enabled,
            "verified": two_factor.is_verified,
            "backup_codes_remaining": backup_count,
            "enabled_at": two_factor.enabled_at.isoformat() if two_factor.enabled_at else None,
            "last_used_at": two_factor.last_used_at.isoformat() if two_factor.last_used_at else None,
        }

    async def is_enabled(self, user_id: int) -> bool:
        """
        Check if 2FA is enabled for a user.

        Args:
            user_id: User ID

        Returns:
            True if 2FA is enabled and verified
        """
        two_factor = await self._get_two_factor(user_id)
        return two_factor is not None and two_factor.is_enabled and two_factor.is_verified

    async def regenerate_backup_codes(self, user: User, code: str) -> list[str]:
        """
        Regenerate backup codes for a user.

        Args:
            user: User object
            code: Current TOTP code for verification

        Returns:
            List of new backup codes

        Raises:
            TwoFactorInvalidException: If code is invalid
            ValidationException: If 2FA not enabled
        """
        two_factor = await self._get_two_factor(user.user_id)

        if not two_factor or not two_factor.is_enabled:
            raise ValidationException(
                message="Two-factor authentication is not enabled."
            )

        # Verify the code
        if not self._verify_totp(two_factor.secret_key, code):
            raise TwoFactorInvalidException()

        # Generate new backup codes
        backup_codes = self._generate_backup_codes()
        two_factor.backup_codes = ",".join(backup_codes)

        await self.db.commit()

        return backup_codes

    # ═══════════════════════════════════════════════════════════
    # PRIVATE METHODS
    # ═══════════════════════════════════════════════════════════

    async def _get_two_factor(self, user_id: int) -> TwoFactorAuth | None:
        """Get TwoFactorAuth record for a user."""
        query = select(TwoFactorAuth).where(TwoFactorAuth.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def _verify_totp(self, secret: str, code: str) -> bool:
        """
        Verify a TOTP code.

        Allows for 1 time step before and after current time
        to account for clock drift.
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)

    def _generate_backup_codes(self) -> list[str]:
        """Generate a list of backup codes."""
        codes = []
        for _ in range(self.BACKUP_CODE_COUNT):
            # Generate random bytes and convert to uppercase hex
            raw = secrets.token_hex(self.BACKUP_CODE_LENGTH // 2).upper()
            # Format as XXXX-XXXX
            formatted = f"{raw[:4]}-{raw[4:]}"
            codes.append(formatted)
        return codes
