"""
Database Configuration

Async SQLAlchemy setup with connection pooling and session management.
Supports multiple schemas (core_app, landfill_mgmt, etc.).
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# ═══════════════════════════════════════════════════════════
# DATABASE ENGINE
# ═══════════════════════════════════════════════════════════

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verify connections before using
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ═══════════════════════════════════════════════════════════
# BASE MODEL
# ═══════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# ═══════════════════════════════════════════════════════════
# SCHEMA NAMES
# ═══════════════════════════════════════════════════════════

class SchemaNames:
    """Database schema names for multi-tenant architecture."""
    CORE_APP = "core_app"
    LANDFILL_MGMT = "landfill_mgmt"


# ═══════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions.

    Usage:
        async with get_db_context() as db:
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ═══════════════════════════════════════════════════════════
# DATABASE UTILITIES
# ═══════════════════════════════════════════════════════════

async def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection successful, False otherwise.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def create_schemas() -> None:
    """
    Create database schemas if they don't exist.

    This should be called during application startup.
    """
    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SchemaNames.CORE_APP}"))
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SchemaNames.LANDFILL_MGMT}"))


async def init_db() -> None:
    """
    Initialize database: create schemas and tables.

    Note: In production, use Alembic migrations instead.
    """
    await create_schemas()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
