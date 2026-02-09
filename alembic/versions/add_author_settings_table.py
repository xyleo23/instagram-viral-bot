"""Add users and author_settings tables

Revision ID: add_author_settings
Revises:
Create Date: 2026-02-09

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_author_settings"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "author_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("min_likes", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("max_post_age_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("idx_author_settings_username", "author_settings", ["username"])
    op.create_index("idx_author_settings_admin_id", "author_settings", ["admin_id"])
    op.create_index("idx_author_settings_is_active", "author_settings", ["is_active"])


def downgrade() -> None:
    op.drop_index("idx_author_settings_is_active", table_name="author_settings")
    op.drop_index("idx_author_settings_admin_id", table_name="author_settings")
    op.drop_index("idx_author_settings_username", table_name="author_settings")
    op.drop_table("author_settings")
    op.drop_index("idx_users_telegram_id", table_name="users")
    op.drop_table("users")
