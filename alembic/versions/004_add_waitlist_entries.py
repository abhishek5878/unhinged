"""Add waitlist_entries table for revamped waitlist with city + referral tracking.

Revision ID: 004
Revises: 003
"""

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "waitlist_entries",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("city", sa.String(255), nullable=False),
        sa.Column("referral_code", sa.String(20), nullable=False, unique=True, index=True),
        sa.Column("referred_by", sa.String(20), nullable=True, index=True),
        sa.Column("referral_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("converted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="organic"),
    )


def downgrade() -> None:
    op.drop_table("waitlist_entries")
