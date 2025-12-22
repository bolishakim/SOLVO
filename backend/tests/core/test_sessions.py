"""
Session Management Tests

Tests for user session management functionality.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import assert_success_response, assert_error_response


# ═══════════════════════════════════════════════════════════
# SESSION LISTING TESTS
# ═══════════════════════════════════════════════════════════

class TestSessionListing:
    """Tests for session listing."""

    @pytest.mark.asyncio
    async def test_list_sessions(self, client: AsyncClient, auth_headers):
        """Test listing user sessions."""
        response = await client.get(
            "/api/v1/auth/sessions",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        assert "sessions" in data["data"]
        assert data["data"]["count"] >= 1

    @pytest.mark.asyncio
    async def test_session_contains_metadata(self, client: AsyncClient, auth_headers):
        """Test that sessions contain expected metadata."""
        response = await client.get(
            "/api/v1/auth/sessions",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        session = data["data"]["sessions"][0]
        assert "session_id" in session
        assert "created_at" in session
        assert "expires_at" in session


# ═══════════════════════════════════════════════════════════
# SESSION REVOCATION TESTS
# ═══════════════════════════════════════════════════════════

class TestSessionRevocation:
    """Tests for session revocation."""

    @pytest.mark.asyncio
    async def test_revoke_session(self, client: AsyncClient, test_user, auth_headers):
        """Test revoking a specific session."""
        # First, get sessions
        response = await client.get(
            "/api/v1/auth/sessions",
            headers=auth_headers,
        )
        data = assert_success_response(response)
        session_id = data["data"]["sessions"][0]["session_id"]

        # Revoke the session
        response = await client.delete(
            f"/api/v1/auth/sessions/{session_id}",
            headers=auth_headers,
        )
        assert_success_response(response)

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_session(self, client: AsyncClient, auth_headers):
        """Test revoking a non-existent session."""
        response = await client.delete(
            "/api/v1/auth/sessions/99999",
            headers=auth_headers,
        )
        assert_error_response(response, 404)

    @pytest.mark.asyncio
    async def test_revoke_all_sessions(self, client: AsyncClient, test_user, user_tokens, auth_headers):
        """Test revoking all sessions."""
        # Create additional sessions by logging in again
        await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )

        # Revoke all sessions
        response = await client.post(
            "/api/v1/auth/sessions/revoke-all",
            json={"keep_current": False},
            headers=auth_headers,
        )
        data = assert_success_response(response)
        assert data["data"]["revoked_count"] >= 1

    @pytest.mark.asyncio
    async def test_revoke_all_except_current(self, client: AsyncClient, test_user, user_tokens, auth_headers):
        """Test revoking all sessions except current."""
        # Create additional session
        await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )

        # Revoke all except current
        response = await client.post(
            "/api/v1/auth/sessions/revoke-all",
            json={
                "keep_current": True,
                "current_refresh_token": user_tokens["refresh_token"],
            },
            headers=auth_headers,
        )
        assert_success_response(response)

        # Current session should still work
        response = await client.get(
            "/api/v1/auth/sessions",
            headers=auth_headers,
        )
        assert_success_response(response)


# ═══════════════════════════════════════════════════════════
# SESSION VALIDATION TESTS
# ═══════════════════════════════════════════════════════════

class TestSessionValidation:
    """Tests for session validation behavior."""

    @pytest.mark.asyncio
    async def test_session_expires_after_logout(self, client: AsyncClient, test_user, user_tokens, auth_headers):
        """Test that session is invalid after logout."""
        # Logout
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": user_tokens["refresh_token"]},
            headers=auth_headers,
        )
        assert_success_response(response)

        # Try to refresh token - should fail
        response = await client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": user_tokens["refresh_token"]},
        )
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_multiple_sessions_independent(self, client: AsyncClient, test_user):
        """Test that multiple sessions are independent."""
        # Create first session
        response1 = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        tokens1 = response1.json()["data"]["tokens"]

        # Create second session
        response2 = await client.post(
            "/api/v1/auth/login",
            json={
                "username_or_email": "testuser",
                "password": "TestPass123",
            },
        )
        tokens2 = response2.json()["data"]["tokens"]

        # Logout first session
        await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens1["refresh_token"]},
            headers={"Authorization": f"Bearer {tokens1['access_token']}"},
        )

        # Second session should still work
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens2['access_token']}"},
        )
        assert_success_response(response)
