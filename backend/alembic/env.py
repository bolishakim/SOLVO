"""
Alembic Environment Configuration

Supports migrations with multiple schemas using synchronous engine.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text
from sqlalchemy.engine import Connection

# Import app configuration and models
from app.config import settings
from app.database import Base, SchemaNames

# Import all models to ensure they're registered with Base.metadata
# Core models
from app.core.models import (
    User,
    Role,
    UserRole,
    UserSession,
    TwoFactorAuth,
    Workflow,
    AuditLog,
    DataExport,
)
# Workflow models (will be added later)
# from app.workflows.landfill_mgmt.models import *

# Alembic Config object
config = context.config

# Set database URL from app settings (sync version for Alembic)
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata

# Schemas to include in migrations
SCHEMAS = [SchemaNames.CORE_APP, SchemaNames.LANDFILL_MGMT]


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter which database objects to include in migrations.

    Only include objects from our application schemas.
    """
    if type_ == "table":
        # Include tables from our schemas
        return object.schema in SCHEMAS
    elif type_ == "schema":
        return name in SCHEMAS
    return True


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL script without connecting to database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
        version_table_schema=SchemaNames.CORE_APP,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    # Create schemas if they don't exist
    for schema in SCHEMAS:
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    connection.commit()

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_object=include_object,
        version_table_schema=SchemaNames.CORE_APP,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates a synchronous engine and runs migrations.
    """
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


# Determine which mode to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
