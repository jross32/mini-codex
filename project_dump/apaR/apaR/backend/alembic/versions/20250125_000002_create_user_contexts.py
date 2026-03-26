"""create user contexts

Revision ID: 20250125_000002
Revises: 20250125_000001
Create Date: 2025-01-25 04:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250125_000002"
down_revision = "20250125_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_contexts",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("league_id", sa.String(length=64), nullable=True),
        sa.Column("division_id", sa.String(length=64), nullable=True),
        sa.Column("team_id", sa.String(length=64), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="captain"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("user_contexts")

