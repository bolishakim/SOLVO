"""
Test Configuration and Fixtures

Provides pytest fixtures for database, clients, and authenticated users.
Uses PostgreSQL test database for full schema compatibility.
"""

import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, settings
from app.database import Base, get_db, SchemaNames
from app.main import create_application
from app.core.models import (
    Role, User, RoleNames, RoleCodes, UserRole, UserSession,
    TwoFactorAuth, PasswordResetToken, AuditLog, ActionType, EntityType,
    DataExport, ExportType, ExportStatus, Workflow, DEFAULT_WORKFLOWS, DEFAULT_ROLES
)
from app.shared.security import hash_password


# ═══════════════════════════════════════════════════════════
# TEST CONFIGURATION
# ═══════════════════════════════════════════════════════════

# Use same PostgreSQL database - tests will use transactions for isolation
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)


class TestSettings(Settings):
    """Override settings for testing."""

    DATABASE_URL: str = TEST_DATABASE_URL
    DEBUG: bool = False
    JWT_SECRET_KEY: str = "test-secret-key-for-testing-only-32chars"


# ═══════════════════════════════════════════════════════════
# EVENT LOOP FIXTURE
# ═══════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ═══════════════════════════════════════════════════════════
# DATABASE FIXTURES
# ═══════════════════════════════════════════════════════════

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Creates a new engine per test for proper isolation.
    Uses connection pool with proper cleanup.
    """
    # Create a fresh engine for this test
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    # Create session factory
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Drop existing tables and recreate for clean state
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SchemaNames.CORE_APP}"))
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SchemaNames.LANDFILL_MGMT}"))
        await conn.run_sync(Base.metadata.create_all)

    # Create session for fixtures
    async with session_factory() as session:
        # Store engine and factory in session for fixture access
        session._test_engine = engine
        session._test_session_factory = session_factory
        yield session
        # Ensure all changes are committed for other sessions to see
        await session.commit()

    # Clean up - drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose engine to clean up all connections
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_with_roles(db_session: AsyncSession) -> AsyncSession:
    """
    Database session with default roles pre-created.
    """
    # Create default roles
    roles = [
        Role(
            role_name=RoleNames.ADMIN,
            role_code=RoleCodes.ADMIN,
            description="Full system access"
        ),
        Role(
            role_name=RoleNames.STANDARD_USER,
            role_code=RoleCodes.STANDARD_USER,
            description="Standard user access"
        ),
        Role(
            role_name=RoleNames.VIEWER,
            role_code=RoleCodes.VIEWER,
            description="Read-only access"
        ),
    ]
    for role in roles:
        db_session.add(role)
    await db_session.commit()

    yield db_session


# ═══════════════════════════════════════════════════════════
# APPLICATION & CLIENT FIXTURES
# ═══════════════════════════════════════════════════════════

@pytest_asyncio.fixture(scope="function")
async def app(db_with_roles: AsyncSession):
    """
    Create FastAPI application with test database.
    """
    application = create_application()

    # Get the session factory from the db_session fixture
    session_factory = db_with_roles._test_session_factory

    # Override the database dependency with same commit/rollback behavior
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    application.dependency_overrides[get_db] = override_get_db

    yield application

    # Clean up
    application.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ═══════════════════════════════════════════════════════════
# USER FIXTURES
# ═══════════════════════════════════════════════════════════

@pytest_asyncio.fixture(scope="function")
async def test_user(db_with_roles: AsyncSession) -> User:
    """
    Create a test user with standard role.
    """
    from app.core.models import UserRole
    from sqlalchemy import select

    # Get standard user role
    result = await db_with_roles.execute(
        select(Role).where(Role.role_name == RoleNames.STANDARD_USER)
    )
    standard_role = result.scalar_one()

    # Create user
    user = User(
        username="testuser",
        email="testuser@example.com",
        password_hash=hash_password("TestPass123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True,
    )
    db_with_roles.add(user)
    await db_with_roles.flush()

    # Assign role
    user_role = UserRole(user_id=user.user_id, role_id=standard_role.role_id)
    db_with_roles.add(user_role)
    await db_with_roles.commit()

    # Refresh to load relationships
    await db_with_roles.refresh(user)

    return user


@pytest_asyncio.fixture(scope="function")
async def admin_user(db_with_roles: AsyncSession) -> User:
    """
    Create an admin user.
    """
    from app.core.models import UserRole
    from sqlalchemy import select

    # Get admin role
    result = await db_with_roles.execute(
        select(Role).where(Role.role_name == RoleNames.ADMIN)
    )
    admin_role = result.scalar_one()

    # Create admin user
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("AdminPass123"),
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_verified=True,
    )
    db_with_roles.add(user)
    await db_with_roles.flush()

    # Assign role
    user_role = UserRole(user_id=user.user_id, role_id=admin_role.role_id)
    db_with_roles.add(user_role)
    await db_with_roles.commit()

    # Refresh to load relationships
    await db_with_roles.refresh(user)

    return user


# ═══════════════════════════════════════════════════════════
# AUTHENTICATION FIXTURES
# ═══════════════════════════════════════════════════════════

@pytest_asyncio.fixture(scope="function")
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """
    Get authentication headers for a standard user.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "TestPass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    access_token = data["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture(scope="function")
async def admin_auth_headers(client: AsyncClient, admin_user: User) -> dict:
    """
    Get authentication headers for an admin user.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "admin",
            "password": "AdminPass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    access_token = data["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture(scope="function")
async def user_tokens(client: AsyncClient, test_user: User) -> dict:
    """
    Get both access and refresh tokens for a standard user.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "TestPass123",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["tokens"]


# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

def assert_success_response(response, expected_status: int = 200):
    """Assert that a response is successful."""
    assert response.status_code == expected_status
    data = response.json()
    assert data.get("success") is True
    return data


def assert_error_response(response, expected_status: int, error_code: str = None):
    """Assert that a response is an error."""
    assert response.status_code == expected_status
    data = response.json()
    assert data.get("success") is False
    if error_code:
        assert data.get("error", {}).get("code") == error_code
    return data
