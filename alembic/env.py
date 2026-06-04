"""
CONCEPT: Alembic Migrations (Async)
======================================
Alembic tracks database schema changes as versioned migration scripts.
Instead of running CREATE TABLE manually, you define the change in a
migration file and Alembic applies it in order.

Workflow:
  1. Change your SQLAlchemy model (add a column, rename, etc.)
  2. alembic revision --autogenerate -m "add column X"  → generates migration file
  3. alembic upgrade head  → applies the migration to the DB
  4. alembic downgrade -1  → roll back one migration

Async setup requires run_async_migrations() — Alembic's default runner
is sync, so we run the async version in asyncio.run().
"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import Base so Alembic can see all models for autogenerate
from app.database import Base
from app.config import settings
# Import all models so they're registered with Base.metadata
import app.models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata tells --autogenerate what the desired schema is
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL scripts)."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations with an async engine."""
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
