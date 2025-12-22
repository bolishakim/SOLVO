"""
User Management Tests

Tests for user CRUD operations and admin user management.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_success_response, assert_error_response


# ═══════════════════════════════════════════════════════════
# ADMIN USER MANAGEMENT TESTS
# ═══════════════════════════════════════════════════════════

class TestAdminUserManagement:
    """Tests for admin user management endpoints."""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test listing users as admin."""
        response = await client.get(
            "/api/v1/admin/users",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # API returns list directly in data, pagination in separate key
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2  # admin + test_user
        assert "pagination" in data
        assert data["pagination"]["total_items"] >= 2

    @pytest.mark.asyncio
    async def test_list_users_as_standard_user(self, client: AsyncClient, auth_headers):
        """Test that standard users cannot list all users."""
        response = await client.get(
            "/api/v1/admin/users",
            headers=auth_headers,
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_user_by_id_as_admin(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test getting a specific user by ID as admin."""
        response = await client.get(
            f"/api/v1/admin/users/{test_user.user_id}",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        assert data["data"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, client: AsyncClient, admin_auth_headers):
        """Test getting a non-existent user."""
        response = await client.get(
            "/api/v1/admin/users/99999",
            headers=admin_auth_headers,
        )
        assert_error_response(response, 404)

    @pytest.mark.asyncio
    async def test_update_user_as_admin(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test updating a user as admin."""
        response = await client.put(
            f"/api/v1/admin/users/{test_user.user_id}",
            json={
                "first_name": "Updated",
                "last_name": "Name",
            },
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        assert data["data"]["first_name"] == "Updated"
        assert data["data"]["last_name"] == "Name"

    @pytest.mark.asyncio
    async def test_deactivate_user_as_admin(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test deactivating a user as admin."""
        response = await client.delete(
            f"/api/v1/admin/users/{test_user.user_id}",
            headers=admin_auth_headers,
        )
        assert_success_response(response)

        # Verify user is deactivated
        response = await client.get(
            f"/api/v1/admin/users/{test_user.user_id}",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        assert data["data"]["is_active"] is False

    @pytest.mark.asyncio
    async def test_cannot_deactivate_self(self, client: AsyncClient, admin_auth_headers, admin_user):
        """Test that admin cannot deactivate their own account."""
        response = await client.delete(
            f"/api/v1/admin/users/{admin_user.user_id}",
            headers=admin_auth_headers,
        )
        # Should fail with validation error or forbidden
        assert response.status_code in [400, 403]


# ═══════════════════════════════════════════════════════════
# ROLE MANAGEMENT TESTS
# ═══════════════════════════════════════════════════════════

class TestRoleManagement:
    """Tests for role management."""

    @pytest.mark.asyncio
    async def test_list_roles_as_admin(self, client: AsyncClient, admin_auth_headers):
        """Test listing available roles as admin."""
        response = await client.get(
            "/api/v1/admin/roles",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # API returns list of roles directly in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 3  # Admin, Standard User, Viewer

    @pytest.mark.asyncio
    async def test_get_user_roles(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test getting roles for a specific user."""
        response = await client.get(
            f"/api/v1/admin/users/{test_user.user_id}/roles",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        # API returns list of roles directly in data
        roles = data["data"]
        assert isinstance(roles, list)
        role_names = [r["role_name"] if isinstance(r, dict) else r for r in roles]
        assert "Standard User" in role_names

    @pytest.mark.asyncio
    async def test_assign_role_to_user(self, client: AsyncClient, admin_auth_headers, test_user, db_with_roles):
        """Test assigning a role to a user."""
        from sqlalchemy import select
        from app.core.models import Role, RoleNames

        # Get viewer role ID
        result = await db_with_roles.execute(
            select(Role).where(Role.role_name == RoleNames.VIEWER)
        )
        viewer_role = result.scalar_one()

        response = await client.post(
            f"/api/v1/admin/users/{test_user.user_id}/roles",
            json={"role_id": viewer_role.role_id},
            headers=admin_auth_headers,
        )
        assert_success_response(response)

    @pytest.mark.asyncio
    async def test_remove_role_from_user(self, client: AsyncClient, admin_auth_headers, test_user, db_with_roles):
        """Test removing a role from a user."""
        from sqlalchemy import select
        from app.core.models import Role, RoleNames

        # First, add a second role so we can remove one
        result = await db_with_roles.execute(
            select(Role).where(Role.role_name == RoleNames.VIEWER)
        )
        viewer_role = result.scalar_one()

        # Add viewer role first
        await client.post(
            f"/api/v1/admin/users/{test_user.user_id}/roles",
            json={"role_id": viewer_role.role_id},
            headers=admin_auth_headers,
        )

        # Now remove it
        response = await client.delete(
            f"/api/v1/admin/users/{test_user.user_id}/roles/{viewer_role.role_id}",
            headers=admin_auth_headers,
        )
        assert_success_response(response)


# ═══════════════════════════════════════════════════════════
# ADMIN STATS TESTS
# ═══════════════════════════════════════════════════════════

class TestAdminStats:
    """Tests for admin statistics."""

    @pytest.mark.asyncio
    async def test_get_admin_stats(self, client: AsyncClient, admin_auth_headers, test_user):
        """Test getting admin statistics."""
        response = await client.get(
            "/api/v1/admin/stats",
            headers=admin_auth_headers,
        )
        data = assert_success_response(response)
        assert "total_users" in data["data"]
        assert "active_users" in data["data"]

    @pytest.mark.asyncio
    async def test_get_admin_stats_as_standard_user(self, client: AsyncClient, auth_headers):
        """Test that standard users cannot access admin stats."""
        response = await client.get(
            "/api/v1/admin/stats",
            headers=auth_headers,
        )
        assert response.status_code == 403
