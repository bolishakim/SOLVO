"""
Two-Factor Authentication Schemas

Request and response schemas for 2FA operations.
"""

from pydantic import BaseModel, Field, field_validator


# ═══════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════


class TwoFactorSetupRequest(BaseModel):
    """Schema for initiating 2FA setup."""

    # No fields needed - user ID comes from token
    pass


class TwoFactorVerifyRequest(BaseModel):
    """Schema for verifying 2FA code during setup or login."""

    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit TOTP code from authenticator app",
        examples=["123456"],
    )

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Code must contain only digits")
        return v


class TwoFactorDisableRequest(BaseModel):
    """Schema for disabling 2FA."""

    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit TOTP code to confirm disable",
        examples=["123456"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Current password for additional verification",
    )

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Code must contain only digits")
        return v


class TwoFactorLoginRequest(BaseModel):
    """Schema for completing login with 2FA."""

    temp_token: str = Field(
        ...,
        description="Temporary token from initial login",
    )
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit TOTP code",
        examples=["123456"],
    )

    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Code must contain only digits")
        return v


class BackupCodeVerifyRequest(BaseModel):
    """Schema for verifying with backup code."""

    temp_token: str = Field(
        ...,
        description="Temporary token from initial login",
    )
    backup_code: str = Field(
        ...,
        min_length=8,
        max_length=12,
        description="One-time backup code",
        examples=["ABCD-EFGH"],
    )


# ═══════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════


class TwoFactorSetupResponse(BaseModel):
    """Schema for 2FA setup response with QR code."""

    success: bool = Field(default=True)
    data: dict = Field(
        ...,
        description="Contains secret, QR code URI, and provisioning URI",
    )
    message: str = Field(default="Scan the QR code with your authenticator app")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "secret": "JBSWY3DPEHPK3PXP",
                    "qr_code_uri": "otpauth://totp/LandfillMgmt:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=LandfillMgmt",
                    "manual_entry_key": "JBSWY3DPEHPK3PXP",
                },
                "message": "Scan the QR code with your authenticator app",
            }
        }


class TwoFactorVerifyResponse(BaseModel):
    """Schema for 2FA verification response."""

    success: bool = Field(default=True)
    data: dict = Field(
        ...,
        description="Contains verification status and backup codes (on first enable)",
    )
    message: str = Field(default="Two-factor authentication enabled")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "enabled": True,
                    "backup_codes": [
                        "ABCD-EFGH",
                        "IJKL-MNOP",
                        "QRST-UVWX",
                        "YZ12-3456",
                        "7890-ABCD",
                    ],
                },
                "message": "Two-factor authentication enabled. Save your backup codes!",
            }
        }


class TwoFactorStatusResponse(BaseModel):
    """Schema for 2FA status check response."""

    success: bool = Field(default=True)
    data: dict = Field(
        ...,
        description="Contains 2FA status information",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "enabled": True,
                    "verified": True,
                    "backup_codes_remaining": 5,
                    "enabled_at": "2024-12-19T10:30:00Z",
                    "last_used_at": "2024-12-19T14:22:00Z",
                },
            }
        }


class TwoFactorDisableResponse(BaseModel):
    """Schema for 2FA disable response."""

    success: bool = Field(default=True)
    data: dict = Field(default_factory=dict)
    message: str = Field(default="Two-factor authentication disabled")


class BackupCodesResponse(BaseModel):
    """Schema for regenerating backup codes."""

    success: bool = Field(default=True)
    data: dict = Field(
        ...,
        description="Contains new backup codes",
    )
    message: str = Field(default="New backup codes generated. Save them securely!")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "backup_codes": [
                        "ABCD-EFGH",
                        "IJKL-MNOP",
                        "QRST-UVWX",
                        "YZ12-3456",
                        "7890-ABCD",
                    ],
                },
                "message": "New backup codes generated. Save them securely!",
            }
        }
