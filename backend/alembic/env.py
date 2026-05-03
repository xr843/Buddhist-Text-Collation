"""Alembic environment.

Pulls the connection URL from app.core.config.settings so the same value
that the app uses at runtime drives migrations — no duplicate config.

asyncpg URLs are converted to psycopg2 for migrations because Alembic's
runner is sync; this is the standard pattern for SQLAlchemy async apps.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

# IMPORTANT: must import _url_compat before anything that touches
# app.core.database — see that module's docstring.
from app import _alembic_url_compat  # noqa: F401

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402
from app import models  # noqa: F401,E402  ensure all model modules are imported


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _resolve_url() -> str:
    url = settings.DATABASE_URL
    # Alembic's offline mode + the sync engine_from_config path both want
    # a sync driver. asyncpg → psycopg2; aiosqlite → pysqlite.
    return (
        url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        .replace("sqlite+aiosqlite://", "sqlite://")
    )


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=_resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online_sync() -> None:
    """Sync online runner — used when DATABASE_URL is already a sync URL."""
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = _resolve_url()
    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        _do_run_migrations(connection)


async def run_migrations_online_async() -> None:
    """Async online runner — used when DATABASE_URL keeps an async driver."""
    from sqlalchemy.ext.asyncio import create_async_engine

    connectable: AsyncEngine = create_async_engine(
        settings.DATABASE_URL, poolclass=pool.NullPool
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
elif "+asyncpg" in settings.DATABASE_URL or "+aiosqlite" in settings.DATABASE_URL:
    asyncio.run(run_migrations_online_async())
else:
    run_migrations_online_sync()
