"""Shim that ensures DATABASE_URL carries an async driver before
`app.core.database` (which builds an async engine at import time) is
loaded by either `env.py` or any migration script.

Importing this module unconditionally rewrites sync URLs (psycopg2,
pysqlite) to their async equivalents in `os.environ`. The original
sync URL is also exported as `ORIGINAL_DATABASE_URL` for callers that
need the sync-driver form (e.g., Alembic's sync runner).
"""
from __future__ import annotations

import os

ORIGINAL_DATABASE_URL = os.environ.get("DATABASE_URL", "")

if ORIGINAL_DATABASE_URL:
    _normalized = (
        ORIGINAL_DATABASE_URL.replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://"
        )
        .replace("postgresql://", "postgresql+asyncpg://")
        .replace("sqlite://", "sqlite+aiosqlite://")
    )
    if _normalized != ORIGINAL_DATABASE_URL:
        os.environ["DATABASE_URL"] = _normalized
