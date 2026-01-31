"""
Alembic environment configuration for DSI database migrations.

Supports both online (connected) and offline (SQL generation) modes.
Uses the same models and engine configuration as the application.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import the DSI models so Alembic can detect schema changes
from infrastructure.db.config import Base, DATABASE_URL_SYNC
from infrastructure.db.models import (  # noqa: F401 - imported for side effects
    User,
    APIKey,
    Submission,
    Quote,
    Referral,
    ModelVersionRecord,
    SignalCache,
    AuditLog,
)

# Alembic Config object
config = context.config

# Override sqlalchemy.url from environment if available
config.set_main_option(
    "sqlalchemy.url",
    os.getenv("DATABASE_URL_SYNC", DATABASE_URL_SYNC),
)

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to a database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Connects to the database and applies migrations directly.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
