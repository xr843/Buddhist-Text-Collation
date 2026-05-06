"""add auth roles and collaboration tables

Revision ID: 0002_auth_admin_collab
Revises: 0001_baseline
Create Date: 2026-05-06
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from alembic import context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_auth_admin_collab"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

json_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def _table_names() -> set[str]:
    if context.is_offline_mode():
        return set()
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table_name: str) -> set[str]:
    if table_name not in _table_names():
        return set()
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    if table_name not in _table_names():
        return set()
    return {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    if index_name in _index_names(table_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    user_columns = _column_names("users")
    if "role" not in user_columns:
        op.add_column(
            "users",
            sa.Column(
                "role",
                sa.Enum("user", "admin", name="userrole", native_enum=False, length=20),
                server_default="user",
                nullable=False,
            ),
        )
    if "avatar_url" not in user_columns:
        op.add_column("users", sa.Column("avatar_url", sa.String(length=500), nullable=True))

    # 0001_baseline intentionally materializes current metadata. On a fresh
    # database it may already create these tables after this model change, while
    # older deployments stamped at 0001 still need this revision to add them.
    if "collab_projects" in _table_names():
        return

    op.create_table(
        "collab_projects",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column(
            "project_type",
            sa.Enum(
                "multi_collation",
                "two_version",
                "punctuation",
                name="collabprojecttype",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "in_progress",
                "completed",
                name="collabprojectstatus",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "visibility",
            sa.Enum(
                "private",
                "shared",
                "public",
                name="projectvisibility",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("data", json_type, nullable=True),
        sa.Column("project_meta", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_collab_projects_created_at", "collab_projects", ["created_at"])
    op.create_index("ix_collab_projects_owner_id", "collab_projects", ["owner_id"])
    op.create_index("ix_collab_projects_status", "collab_projects", ["status"])
    op.create_index("ix_collab_projects_title", "collab_projects", ["title"])
    op.create_index("ix_collab_projects_visibility", "collab_projects", ["visibility"])

    op.create_table(
        "project_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("viewer", "editor", "admin", name="memberrole", native_enum=False, length=32),
            nullable=False,
        ),
        sa.Column("invited_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["collab_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_project_members_id", "project_members", ["id"])
    op.create_index(
        "ix_project_members_project_user",
        "project_members",
        ["project_id", "user_id"],
        unique=True,
    )

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("variant_index", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["collab_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comments_id", "comments", ["id"])
    op.create_index("ix_comments_parent_id", "comments", ["parent_id"])
    op.create_index("ix_comments_project_id", "comments", ["project_id"])
    op.create_index("ix_comments_user_id", "comments", ["user_id"])
    op.create_index("ix_comments_variant_index", "comments", ["variant_index"])

    op.create_table(
        "edit_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "action",
            sa.Enum(
                "create",
                "update",
                "decision",
                "export",
                "delete",
                name="editaction",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("details", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["collab_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_edit_history_action", "edit_history", ["action"])
    op.create_index("ix_edit_history_created_at", "edit_history", ["created_at"])
    op.create_index("ix_edit_history_id", "edit_history", ["id"])
    op.create_index("ix_edit_history_project_id", "edit_history", ["project_id"])
    op.create_index("ix_edit_history_user_id", "edit_history", ["user_id"])


def downgrade() -> None:
    if "edit_history" in _table_names():
        _drop_index_if_exists("ix_edit_history_user_id", "edit_history")
        _drop_index_if_exists("ix_edit_history_project_id", "edit_history")
        _drop_index_if_exists("ix_edit_history_id", "edit_history")
        _drop_index_if_exists("ix_edit_history_created_at", "edit_history")
        _drop_index_if_exists("ix_edit_history_action", "edit_history")
        op.drop_table("edit_history")

    if "comments" in _table_names():
        _drop_index_if_exists("ix_comments_variant_index", "comments")
        _drop_index_if_exists("ix_comments_user_id", "comments")
        _drop_index_if_exists("ix_comments_project_id", "comments")
        _drop_index_if_exists("ix_comments_parent_id", "comments")
        _drop_index_if_exists("ix_comments_id", "comments")
        op.drop_table("comments")

    if "project_members" in _table_names():
        _drop_index_if_exists("ix_project_members_project_user", "project_members")
        _drop_index_if_exists("ix_project_members_id", "project_members")
        op.drop_table("project_members")

    if "collab_projects" in _table_names():
        _drop_index_if_exists("ix_collab_projects_visibility", "collab_projects")
        _drop_index_if_exists("ix_collab_projects_title", "collab_projects")
        _drop_index_if_exists("ix_collab_projects_status", "collab_projects")
        _drop_index_if_exists("ix_collab_projects_owner_id", "collab_projects")
        _drop_index_if_exists("ix_collab_projects_created_at", "collab_projects")
        op.drop_table("collab_projects")

    user_columns = _column_names("users")
    if "avatar_url" in user_columns:
        op.drop_column("users", "avatar_url")
    if "role" in user_columns:
        op.drop_column("users", "role")
