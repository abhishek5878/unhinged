"""add_waitlist_signups

Revision ID: 002
Revises: 001
Create Date: 2026-02-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "waitlist_signups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("partner_email", sa.String(255), nullable=True),
        sa.Column("referral_code", sa.String(20), nullable=False, unique=True),
        sa.Column("referral_code_used", sa.String(20), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="waiting"
        ),
        sa.Column("clerk_user_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_waitlist_signups_email", "waitlist_signups", ["email"]
    )
    op.create_index(
        "ix_waitlist_signups_referral_code",
        "waitlist_signups",
        ["referral_code"],
    )
    op.create_index(
        "ix_waitlist_signups_clerk_user_id",
        "waitlist_signups",
        ["clerk_user_id"],
    )


def downgrade() -> None:
    op.drop_table("waitlist_signups")
