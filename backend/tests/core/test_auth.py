"""
Authentication Tests

Tests for registration, login, logout, password management, and token refresh.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_success_response, assert_error_response


# ═══════════════════════════════════════════════════════════
# REGISTRATION TESTS
# ═══════════════════════════════════════════════════════════

class TestRegistration:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "first_name": "New",
                "last_name": "User",
            },
        )
        data = assert_success_response(response, 201)
        assert data["data"]["username"] == "newuser"
        assert data["data"]["email"] == "newuser@example.com"
        assert "Standard User" in data["data"]["roles"]

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """Test registration with existing username."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",  # Already exists
                "email": "different@example.com",
                "password": "SecurePass123",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert_error_response(response, 409)

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "differentuser",
                "email": "testuser@example.com",  # Already exists
                "password": "SecurePass123",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert_error_response(response, 409)

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "weak",  # Too short
                "first_name": "New",
                "last_name": "User",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "SecurePass123",
                "first_name": "New",
                "last_name": "User",
            },
        )
        assert response.status_code == 400


# ═══════════════════════════════════════════════════════════
# LOGIN TESTS
# ═══════════════════════════════════════════════════════════

class TestLogin:
    """Tests for user login."""

    @pytest.mark.asyncio
    async def test_login_with_username(self, client: AsyncClient, test_user):
        """Test login with username."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        data = assert_success_response(response)
        assert "tokens" in data["data"]
        assert "access_token" in data["data"]["tokens"]
        assert "refresh_token" in data["data"]["tokens"]
        assert data["data"]["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_login_with_email(self, client: AsyncClient, test_user):
        """Test login with email."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser@example.com",
                "password": "TestPass123",
            },
        )
        data = assert_success_response(response)
        assert data["data"]["user"]["email"] == "testuser@example.com"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "WrongPassword123",
            },
        )
        assert_error_response(response, 401)

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "nonexistent",
                "password": "SomePass123",
            },
        )
        assert_error_response(response, 401)

    @pytest.mark.asyncio
    async def test_login_creates_session(self, client: AsyncClient, test_user, auth_headers):
        """Test that login creates a session."""
        response = await client.get(
            "/api/v1/auth/sessions",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        assert data["data"]["count"] >= 1


# ═══════════════════════════════════════════════════════════
# LOGOUT TESTS
# ═══════════════════════════════════════════════════════════

class TestLogout:
    """Tests for user logout."""

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, test_user, user_tokens, auth_headers):
        """Test successful logout."""
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": user_tokens["refresh_token"]},
            headers=auth_headers,
        )
        assert_success_response(response)

    @pytest.mark.asyncio
    async def test_logout_without_auth(self, client: AsyncClient):
        """Test logout without authentication."""
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "some-token"},
        )
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# TOKEN REFRESH TESTS
# ═══════════════════════════════════════════════════════════

class TestTokenRefresh:
    """Tests for token refresh."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, user_tokens):
        """Test successful token refresh."""
        response = await client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": user_tokens["refresh_token"]},
        )
        data = assert_success_response(response)
        assert "access_token" in data["data"]["tokens"]

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test token refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": "invalid-token"},
        )
        assert_error_response(response, 401)


# ═══════════════════════════════════════════════════════════
# PASSWORD CHANGE TESTS
# ═══════════════════════════════════════════════════════════

class TestPasswordChange:
    """Tests for password change."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient, test_user, auth_headers):
        """Test successful password change."""
        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "TestPass123",
                "new_password": "NewSecurePass456",
            },
            headers=auth_headers,
        )
        assert_success_response(response)

        # Verify new password works
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "NewSecurePass456",
            },
        )
        assert_success_response(response)

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers):
        """Test password change with wrong current password."""
        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "WrongPassword",
                "new_password": "NewSecurePass456",
            },
            headers=auth_headers,
        )
        assert_error_response(response, 401)

    @pytest.mark.asyncio
    async def test_change_password_same_password(self, client: AsyncClient, auth_headers):
        """Test password change with same password."""
        response = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "TestPass123",
                "new_password": "TestPass123",  # Same as current
            },
            headers=auth_headers,
        )
        assert_error_response(response, 400)


# ═══════════════════════════════════════════════════════════
# PASSWORD RESET TESTS
# ═══════════════════════════════════════════════════════════

class TestPasswordReset:
    """Tests for password reset flow."""

    @pytest.mark.asyncio
    async def test_forgot_password_existing_email(self, client: AsyncClient, test_user):
        """Test forgot password with existing email."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "testuser@example.com"},
        )
        data = assert_success_response(response)
        # In dev mode, token is returned
        assert "_dev_token" in data["data"]

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """Test forgot password with non-existent email."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        # Should still return success to prevent email enumeration
        assert_success_response(response)

    @pytest.mark.asyncio
    async def test_reset_password_flow(self, client: AsyncClient, test_user):
        """Test complete password reset flow."""
        # Request reset token
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "testuser@example.com"},
        )
        data = assert_success_response(response)
        reset_token = data["data"]["_dev_token"]

        # Reset password
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "ResetPass789",
            },
        )
        assert_success_response(response)

        # Verify new password works
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "ResetPass789",
            },
        )
        assert_success_response(response)

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test password reset with invalid token."""
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid-token",
                "new_password": "NewPassword123",
            },
        )
        assert_error_response(response, 400)


# ═══════════════════════════════════════════════════════════
# SESSION VALIDATION TESTS
# ═══════════════════════════════════════════════════════════

class TestSessionValidation:
    """Tests for session validation."""

    @pytest.mark.asyncio
    async def test_validate_session_success(self, client: AsyncClient, auth_headers):
        """Test successful session validation."""
        response = await client.get(
            "/api/v1/auth/session/validate",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        assert data["data"]["valid"] is True
        assert data["data"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_validate_session_invalid_token(self, client: AsyncClient):
        """Test session validation with invalid token."""
        response = await client.get(
            "/api/v1/auth/session/validate",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# ACCOUNT LOCKOUT TESTS
# ═══════════════════════════════════════════════════════════

class TestAccountLockout:
    """Tests for account lockout functionality."""

    @pytest.mark.asyncio
    async def test_account_lockout_after_failed_attempts(self, client: AsyncClient, test_user):
        """Test that account is locked after too many failed attempts."""
        # Make 5 failed login attempts
        for i in range(5):
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "username_or_email": "testuser",
                    "password": "WrongPassword",
                },
            )
            assert response.status_code == 401

        # 6th attempt should show locked
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "WrongPassword",
            },
        )
        assert response.status_code == 403
        data = response.json()
        assert "locked" in data["error"]["message"].lower()


# ═══════════════════════════════════════════════════════════
# CURRENT USER TESTS
# ═══════════════════════════════════════════════════════════

class TestCurrentUser:
    """Tests for current user endpoints."""

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """Test getting current user profile."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        assert data["data"]["username"] == "testuser"
        assert data["data"]["email"] == "testuser@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_without_auth(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
