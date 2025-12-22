"""
Two-Factor Authentication Tests

Tests for TOTP-based 2FA setup, verification, and management.
"""

import pytest
import pyotp
from httpx import AsyncClient

from tests.conftest import assert_success_response, assert_error_response


# ═══════════════════════════════════════════════════════════
# 2FA SETUP TESTS
# ═══════════════════════════════════════════════════════════

class TestTwoFactorSetup:
    """Tests for 2FA setup."""

    @pytest.mark.asyncio
    async def test_setup_2fa(self, client: AsyncClient, auth_headers):
        """Test initiating 2FA setup."""
        response = await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        assert "secret" in data["data"]
        assert "qr_code_uri" in data["data"]
        assert "manual_entry_key" in data["data"]

    @pytest.mark.asyncio
    async def test_verify_and_enable_2fa(self, client: AsyncClient, auth_headers):
        """Test verifying and enabling 2FA."""
        # Setup 2FA
        response = await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        secret = data["data"]["secret"]

        # Generate valid TOTP code
        totp = pyotp.TOTP(secret)
        code = totp.now()

        # Verify and enable
        response = await client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": code},
            headers=auth_headers,
        )
        data = assert_success_response(response)
        assert data["data"]["enabled"] is True
        assert "backup_codes" in data["data"]
        assert len(data["data"]["backup_codes"]) == 10

    @pytest.mark.asyncio
    async def test_verify_2fa_invalid_code(self, client: AsyncClient, auth_headers):
        """Test 2FA verification with invalid code."""
        # Setup 2FA
        await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )

        # Try to verify with invalid code
        response = await client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": "000000"},
            headers=auth_headers,
        )
        assert_error_response(response, 401)


# ═══════════════════════════════════════════════════════════
# 2FA STATUS TESTS
# ═══════════════════════════════════════════════════════════

class TestTwoFactorStatus:
    """Tests for 2FA status."""

    @pytest.mark.asyncio
    async def test_get_2fa_status_disabled(self, client: AsyncClient, auth_headers):
        """Test getting 2FA status when disabled."""
        response = await client.get(
            "/api/v1/auth/2fa/status",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        assert data["data"]["enabled"] is False

    @pytest.mark.asyncio
    async def test_get_2fa_status_enabled(self, client: AsyncClient, auth_headers):
        """Test getting 2FA status when enabled."""
        # Setup and enable 2FA
        response = await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )
        secret = response.json()["data"]["secret"]
        totp = pyotp.TOTP(secret)

        await client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": totp.now()},
            headers=auth_headers,
        )

        # Check status
        response = await client.get(
            "/api/v1/auth/2fa/status",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        assert data["data"]["enabled"] is True
        assert data["data"]["backup_codes_remaining"] == 10


# ═══════════════════════════════════════════════════════════
# 2FA LOGIN TESTS
# ═══════════════════════════════════════════════════════════

class TestTwoFactorLogin:
    """Tests for 2FA login flow."""

    @pytest.mark.asyncio
    async def test_login_requires_2fa(self, client: AsyncClient, test_user, auth_headers):
        """Test that login requires 2FA when enabled."""
        # Setup and enable 2FA
        response = await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )
        secret = response.json()["data"]["secret"]
        totp = pyotp.TOTP(secret)

        await client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": totp.now()},
            headers=auth_headers,
        )

        # Now login should require 2FA
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        data = assert_success_response(response)
        assert data["data"]["requires_2fa"] is True
        assert "temp_token" in data["data"]

    @pytest.mark.asyncio
    async def test_complete_2fa_login(self, client: AsyncClient, test_user, auth_headers):
        """Test completing login with 2FA."""
        # Setup and enable 2FA
        response = await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )
        secret = response.json()["data"]["secret"]
        totp = pyotp.TOTP(secret)

        await client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": totp.now()},
            headers=auth_headers,
        )

        # Login - get temp token
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        temp_token = response.json()["data"]["temp_token"]

        # Complete login with 2FA
        response = await client.post(
            "/api/v1/auth/login/2fa",
            json={
                "temp_token": temp_token,
                "code": totp.now(),
            },
        )
        data = assert_success_response(response)
        assert "tokens" in data["data"]
        assert "access_token" in data["data"]["tokens"]

    @pytest.mark.asyncio
    async def test_2fa_login_invalid_code(self, client: AsyncClient, test_user, auth_headers):
        """Test 2FA login with invalid code."""
        # Setup and enable 2FA
        response = await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )
        secret = response.json()["data"]["secret"]
        totp = pyotp.TOTP(secret)

        await client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": totp.now()},
            headers=auth_headers,
        )

        # Login - get temp token
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        temp_token = response.json()["data"]["temp_token"]

        # Try to complete with invalid code
        response = await client.post(
            "/api/v1/auth/login/2fa",
            json={
                "temp_token": temp_token,
                "code": "000000",
            },
        )
        assert_error_response(response, 401)


# ═══════════════════════════════════════════════════════════
# BACKUP CODE TESTS
# ═══════════════════════════════════════════════════════════

class TestBackupCodes:
    """Tests for backup code functionality."""

    @pytest.mark.asyncio
    async def test_login_with_backup_code(self, client: AsyncClient, test_user, auth_headers):
        """Test logging in with a backup code."""
        # Setup and enable 2FA
        response = await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )
        secret = response.json()["data"]["secret"]
        totp = pyotp.TOTP(secret)

        response = await client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": totp.now()},
            headers=auth_headers,
        )
        backup_codes = response.json()["data"]["backup_codes"]

        # Login - get temp token
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        temp_token = response.json()["data"]["temp_token"]

        # Login with backup code
        response = await client.post(
            "/api/v1/auth/login/backup-code",
            json={
                "temp_token": temp_token,
                "backup_code": backup_codes[0],
            },
        )
        data = assert_success_response(response)
        assert "tokens" in data["data"]

    @pytest.mark.asyncio
    async def test_regenerate_backup_codes(self, client: AsyncClient, auth_headers):
        """Test regenerating backup codes."""
        # Setup and enable 2FA
        response = await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )
        secret = response.json()["data"]["secret"]
        totp = pyotp.TOTP(secret)

        await client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": totp.now()},
            headers=auth_headers,
        )

        # Regenerate backup codes
        response = await client.post(
            "/api/v1/auth/2fa/backup-codes/regenerate",
            json={"code": totp.now()},
            headers=auth_headers,
        )
        data = assert_success_response(response)
        assert "backup_codes" in data["data"]
        assert len(data["data"]["backup_codes"]) == 10


# ═══════════════════════════════════════════════════════════
# 2FA DISABLE TESTS
# ═══════════════════════════════════════════════════════════

class TestTwoFactorDisable:
    """Tests for disabling 2FA."""

    @pytest.mark.asyncio
    async def test_disable_2fa(self, client: AsyncClient, auth_headers):
        """Test disabling 2FA."""
        # Setup and enable 2FA
        response = await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )
        secret = response.json()["data"]["secret"]
        totp = pyotp.TOTP(secret)

        await client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": totp.now()},
            headers=auth_headers,
        )

        # Disable 2FA
        response = await client.post(
            "/api/v1/auth/2fa/disable",
            json={
                "code": totp.now(),
                "password": "TestPass123",
            },
            headers=auth_headers,
        )
        assert_success_response(response)

        # Verify it's disabled
        response = await client.get(
            "/api/v1/auth/2fa/status",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        assert data["data"]["enabled"] is False

    @pytest.mark.asyncio
    async def test_disable_2fa_wrong_password(self, client: AsyncClient, auth_headers):
        """Test disabling 2FA with wrong password."""
        # Setup and enable 2FA
        response = await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )
        secret = response.json()["data"]["secret"]
        totp = pyotp.TOTP(secret)

        await client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": totp.now()},
            headers=auth_headers,
        )

        # Try to disable with wrong password
        response = await client.post(
            "/api/v1/auth/2fa/disable",
            json={
                "code": totp.now(),
                "password": "WrongPassword",
            },
            headers=auth_headers,
        )
        assert_error_response(response, 401)
