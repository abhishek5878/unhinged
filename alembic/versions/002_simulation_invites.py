"""simulation_invites table

Revision ID: 002
Revises: 001
Create Date: 2026-02-21

"""
from typing import Sequence, Union
from datetime import datetime, timezone, timedelta

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "simulation_invites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("token", sa.String(16), nullable=False, unique=True, index=True),
        sa.Column(
            "inviter_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id"),
            nullable=False,
        ),
        sa.Column(
            "invitee_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "simulation_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("simulation_runs.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("simulation_invites")
