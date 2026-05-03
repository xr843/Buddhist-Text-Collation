"""baseline: snapshot of the current SQLAlchemy schema

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-03

This is a "baseline" migration — it materializes the entire schema as
defined by `app.models.*` at the time Alembic was introduced. We use
`Base.metadata.create_all` rather than hand-written DDL because there
were no prior migrations and no production schema-of-truth other than
the ORM models themselves.

For pre-existing deployments whose tables were created via
`Base.metadata.create_all` at app startup (the development fallback in
`app/core/database.py`), run:

    alembic stamp 0001_baseline

so Alembic records the schema as already applied without re-running it.

All future schema changes go through normal `alembic revision --autogenerate`
against this baseline.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# Ensure DATABASE_URL is async-compatible before app.core.database loads
# (it builds an async engine at import time). Same shim env.py uses.
from app import _alembic_url_compat  # noqa: F401

from app.core.database import Base  # noqa: E402
from app import models  # noqa: F401,E402  ensure all models are imported

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
