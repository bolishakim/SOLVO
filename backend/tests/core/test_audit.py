"""
Audit Logging Tests

Tests for audit log functionality.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_success_response, assert_error_response


# ═══════════════════════════════════════════════════════════
# AUDIT LOG ACCESS TESTS
# ═══════════════════════════════════════════════════════════

class TestAuditLogAccess:
    """Tests for audit log access."""

    @pytest.mark.asyncio
    async def test_list_audit_logs_as_admin(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test listing audit logs as admin."""
        # First, perform an action that creates an audit log
        await client.get(
            "/api/v1/auth/me",
            headers=admin_auth_headers,
        )

        # List audit logs
        response = await client.get(
            "/api/v1/admin/audit-logs",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # API returns list directly in data, pagination in separate key
        assert isinstance(data["data"], list)
        assert "pagination" in data

    @pytest.mark.asyncio
    async def test_list_audit_logs_as_standard_user(self, client: AsyncClient, auth_headers):
        """Test that standard users cannot access audit logs."""
        response = await client.get(
            "/api/v1/admin/audit-logs",
            headers=auth_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_filter_audit_logs_by_user(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test filtering audit logs by user ID."""
        response = await client.get(
            f"/api/v1/admin/audit-logs?user_id={test_user.user_id}",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # API returns list directly in data
        # All returned logs should be for the specified user
        for item in data["data"]:
            assert item["user_id"] == test_user.user_id

    @pytest.mark.asyncio
    async def test_filter_audit_logs_by_action_type(self, client: AsyncClient, admin_auth_headers):
        """Test filtering audit logs by action type."""
        response = await client.get(
            "/api/v1/admin/audit-logs?action_type=LOGIN",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # API returns list directly in data
        # All returned logs should have the specified action type
        for item in data["data"]:
            assert item["action_type"] == "LOGIN"


# ═══════════════════════════════════════════════════════════
# AUDIT LOG STATS TESTS
# ═══════════════════════════════════════════════════════════

class TestAuditLogStats:
    """Tests for audit log statistics."""

    @pytest.mark.asyncio
    async def test_get_audit_stats(self, client: AsyncClient, admin_auth_headers):
        """Test getting audit log statistics."""
        response = await client.get(
            "/api/v1/admin/audit-logs/stats",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        assert "total_logs" in data["data"]
        # API returns by_action_type, not actions_by_type
        assert "by_action_type" in data["data"]


# ═══════════════════════════════════════════════════════════
# LOGIN HISTORY TESTS
# ═══════════════════════════════════════════════════════════

class TestLoginHistory:
    """Tests for login history."""

    @pytest.mark.asyncio
    async def test_get_login_history(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test getting login history."""
        # Create some login events
        await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )

        response = await client.get(
            "/api/v1/admin/audit-logs/login-history",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # API returns logs and count, not items
        assert "logs" in data["data"]
        assert "count" in data["data"]

    @pytest.mark.asyncio
    async def test_get_login_history_for_user(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test getting login history for specific user."""
        response = await client.get(
            f"/api/v1/admin/audit-logs/user/{test_user.user_id}",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # API returns logs and count for specific user
        assert "logs" in data["data"]
        assert "user_id" in data["data"]


# ═══════════════════════════════════════════════════════════
# AUDIT LOG TYPES TESTS
# ═══════════════════════════════════════════════════════════

class TestAuditLogTypes:
    """Tests for audit log type endpoints."""

    @pytest.mark.asyncio
    async def test_get_action_types(self, client: AsyncClient, admin_auth_headers):
        """Test getting available action types."""
        response = await client.get(
            "/api/v1/admin/audit-logs/action-types",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # API returns list directly in data
        action_types = data["data"]
        assert isinstance(action_types, list)
        # Should include common action types
        assert "LOGIN" in action_types
        assert "LOGOUT" in action_types

    @pytest.mark.asyncio
    async def test_get_entity_types(self, client: AsyncClient, admin_auth_headers):
        """Test getting available entity types."""
        response = await client.get(
            "/api/v1/admin/audit-logs/entity-types",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # API returns list directly in data
        entity_types = data["data"]
        assert isinstance(entity_types, list)
        # Should include common entity types
        assert "USER" in entity_types
        assert "SESSION" in entity_types


# ═══════════════════════════════════════════════════════════
# AUDIT LOG CREATION TESTS
# ═══════════════════════════════════════════════════════════

class TestAuditLogCreation:
    """Tests for automatic audit log creation."""

    @pytest.mark.asyncio
    async def test_login_creates_audit_log(self, client: AsyncClient, test_user, admin_auth_headers):
        """Test that login creates an audit log entry."""
        # Login as test user
        await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )

        # Check audit logs - API returns list directly in data
        # Query ALL login events (admin login is also included)
        response = await client.get(
            "/api/v1/admin/audit-logs?action_type=LOGIN",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # Should have at least 2 logins: admin (for admin_auth_headers) and test_user
        assert len(data["data"]) >= 2

    @pytest.mark.asyncio
    async def test_registration_creates_audit_log(self, client: AsyncClient, admin_auth_headers):
        """Test that registration creates an audit log entry."""
        # Register a new user
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "audituser",
                "email": "audituser@example.com",
                "password": "SecurePass123",
                "first_name": "Audit",
                "last_name": "User",
            },
        )
        # Verify registration succeeded
        assert reg_response.status_code == 201

        # Check audit logs - API returns list directly in data
        response = await client.get(
            "/api/v1/admin/audit-logs?action_type=REGISTER",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # Should have at least one registration log
        assert len(data["data"]) >= 1
        assert data["data"][0]["action_type"] == "REGISTER"

    @pytest.mark.asyncio
    async def test_failed_login_creates_audit_log(self, client: AsyncClient, test_user, admin_auth_headers):
        """Test that failed login creates an audit log entry."""
        # Failed login attempt
        failed_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "WrongPassword",
            },
        )
        # Verify login failed
        assert failed_response.status_code == 401

        # Check audit logs - API returns list directly in data
        # Query for LOGIN_FAILED action type
        response = await client.get(
            "/api/v1/admin/audit-logs?action_type=LOGIN_FAILED",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # Should have at least one failed login log
        assert len(data["data"]) >= 1
        assert data["data"][0]["action_type"] == "LOGIN_FAILED"
