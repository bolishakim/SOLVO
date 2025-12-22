"""
Integration Tests

End-to-end tests for complete workflows.
"""

import pytest
import pyotp
from httpx import AsyncClient

from tests.conftest import assert_success_response, assert_error_response


# ═══════════════════════════════════════════════════════════
# FULL AUTH FLOW TESTS
# ═══════════════════════════════════════════════════════════

class TestFullAuthFlow:
    """Integration tests for complete authentication flows."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_registration_to_logout_flow(self, client: AsyncClient):
        """Test complete flow from registration to logout."""
        # 1. Register
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "flowuser",
                "email": "flowuser@example.com",
                "password": "FlowPass123",
                "first_name": "Flow",
                "last_name": "User",
            },
        )
        data = assert_success_response(response, 201)
        user_id = data["data"]["user_id"]

        # 2. Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "flowuser",
                "password": "FlowPass123",
            },
        )
        data = assert_success_response(response)
        access_token = data["data"]["tokens"]["access_token"]
        refresh_token = data["data"]["tokens"]["refresh_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 3. Access protected resource
        response = await client.get("/api/v1/auth/me", headers=headers)
        data = assert_success_response(response)
        assert data["data"]["username"] == "flowuser"

        # 4. Refresh token
        response = await client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": refresh_token},
        )
        data = assert_success_response(response)
        new_access_token = data["data"]["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {new_access_token}"}

        # 5. Logout
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers=headers,
        )
        assert_success_response(response)

        # 6. Verify refresh token is invalidated
        response = await client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_2fa_flow(self, client: AsyncClient, test_user, auth_headers):
        """Test complete 2FA setup and login flow."""
        # 1. Setup 2FA
        response = await client.post(
            "/api/v1/auth/2fa/setup",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        secret = data["data"]["secret"]
        totp = pyotp.TOTP(secret)

        # 2. Verify and enable 2FA
        response = await client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": totp.now()},
            headers=auth_headers,
        )
        data = assert_success_response(response)
        backup_codes = data["data"]["backup_codes"]
        assert len(backup_codes) == 10

        # 3. Login now requires 2FA
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        data = assert_success_response(response)
        assert data["data"]["requires_2fa"] is True
        temp_token = data["data"]["temp_token"]

        # 4. Complete login with TOTP
        response = await client.post(
            "/api/v1/auth/login/2fa",
            json={
                "temp_token": temp_token,
                "code": totp.now(),
            },
        )
        data = assert_success_response(response)
        new_access_token = data["data"]["tokens"]["access_token"]
        new_headers = {"Authorization": f"Bearer {new_access_token}"}

        # 5. Verify access works
        response = await client.get("/api/v1/auth/me", headers=new_headers)
        assert_success_response(response)

        # 6. Disable 2FA
        response = await client.post(
            "/api/v1/auth/2fa/disable",
            json={
                "code": totp.now(),
                "password": "TestPass123",
            },
            headers=new_headers,
        )
        assert_success_response(response)

        # 7. Login no longer requires 2FA
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        data = assert_success_response(response)
        assert "tokens" in data["data"]
        assert data["data"].get("requires_2fa") is not True


# ═══════════════════════════════════════════════════════════
# PASSWORD RESET FLOW TESTS
# ═══════════════════════════════════════════════════════════

class TestPasswordResetFlow:
    """Integration tests for password reset flow."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_password_reset_flow(self, client: AsyncClient, test_user):
        """Test complete password reset flow."""
        # 1. Request password reset
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "testuser@example.com"},
        )
        data = assert_success_response(response)
        reset_token = data["data"]["_dev_token"]

        # 2. Reset password
        new_password = "NewResetPass456"
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": new_password,
            },
        )
        assert_success_response(response)

        # 3. Verify old password no longer works
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        assert response.status_code == 401

        # 4. Verify new password works
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": new_password,
            },
        )
        assert_success_response(response)

        # 5. Verify reset token cannot be reused
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": "AnotherPass789",
            },
        )
        assert_error_response(response, 400)


# ═══════════════════════════════════════════════════════════
# ROLE-BASED ACCESS CONTROL TESTS
# ═══════════════════════════════════════════════════════════

class TestRoleBasedAccess:
    """Integration tests for role-based access control."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_admin_only_endpoints(self, client: AsyncClient, auth_headers, admin_auth_headers):
        """Test that admin endpoints are restricted."""
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/stats",
            "/api/v1/admin/audit-logs",
            "/api/v1/admin/roles",
        ]

        for endpoint in admin_endpoints:
            # Standard user should be denied
            response = await client.get(endpoint, headers=auth_headers)
            assert response.status_code == 403, f"Standard user should not access {endpoint}"

            # Admin should be allowed
            response = await client.get(endpoint, headers=admin_auth_headers)
            assert response.status_code == 200, f"Admin should access {endpoint}"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_role_assignment_affects_access(self, client: AsyncClient, test_user, admin_auth_headers, db_with_roles):
        """Test that assigning roles changes access."""
        from sqlalchemy import select
        from app.core.models import Role, RoleNames

        # Get admin role
        result = await db_with_roles.execute(
            select(Role).where(Role.role_name == RoleNames.ADMIN)
        )
        admin_role = result.scalar_one()

        # Get auth for test user
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        access_token = response.json()["data"]["tokens"]["access_token"]
        user_headers = {"Authorization": f"Bearer {access_token}"}

        # Initially cannot access admin endpoint
        response = await client.get("/api/v1/admin/users", headers=user_headers)
        assert response.status_code == 403

        # Assign admin role
        response = await client.post(
            f"/api/v1/admin/users/{test_user.user_id}/roles",
            json={"role_id": admin_role.role_id},
            headers=admin_auth_headers,
        )
        assert_success_response(response)

        # Re-login to get updated token with new roles
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        access_token = response.json()["data"]["tokens"]["access_token"]
        user_headers = {"Authorization": f"Bearer {access_token}"}

        # Now can access admin endpoint
        response = await client.get("/api/v1/admin/users", headers=user_headers)
        assert_success_response(response)


# ═══════════════════════════════════════════════════════════
# SESSION MANAGEMENT FLOW TESTS
# ═══════════════════════════════════════════════════════════

class TestSessionManagement:
    """Integration tests for session management."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_device_sessions(self, client: AsyncClient, test_user):
        """Test managing sessions from multiple devices."""
        # Login from "device 1"
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        tokens1 = response.json()["data"]["tokens"]
        headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}

        # Login from "device 2"
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        tokens2 = response.json()["data"]["tokens"]
        headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}

        # Login from "device 3"
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        tokens3 = response.json()["data"]["tokens"]
        headers3 = {"Authorization": f"Bearer {tokens3['access_token']}"}

        # Check we have 3 sessions
        response = await client.get("/api/v1/auth/sessions", headers=headers1)
        data = assert_success_response(response)
        assert data["data"]["count"] == 3

        # Revoke all except current (device 1)
        response = await client.post(
            "/api/v1/auth/sessions/revoke-all",
            json={
                "keep_current": True,
                "current_refresh_token": tokens1["refresh_token"],
            },
            headers=headers1,
        )
        data = assert_success_response(response)
        assert data["data"]["revoked_count"] == 2

        # Device 1 still works
        response = await client.get("/api/v1/auth/me", headers=headers1)
        assert_success_response(response)

        # Device 2 and 3 refresh tokens should fail
        response = await client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": tokens2["refresh_token"]},
        )
        assert response.status_code in [401, 403]


# ═══════════════════════════════════════════════════════════
# SECURITY MIDDLEWARE TESTS
# ═══════════════════════════════════════════════════════════

class TestSecurityMiddleware:
    """Integration tests for security middleware."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_security_headers_present(self, client: AsyncClient):
        """Test that security headers are present on all responses."""
        response = await client.get("/health")

        # Check security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Referrer-Policy" in response.headers

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_request_id_propagated(self, client: AsyncClient):
        """Test that request ID is generated and returned."""
        response = await client.get("/health")
        assert "X-Request-ID" in response.headers

        # Test that provided request ID is propagated
        custom_id = "test-request-12345"
        response = await client.get(
            "/health",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers.get("X-Request-ID") == custom_id

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rate_limit_headers(self, client: AsyncClient, auth_headers):
        """Test that rate limit headers are present."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
