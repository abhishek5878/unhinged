"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-02-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user_profiles (embedding stored as JSONB float array for portability)
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("shadow_vector", postgresql.JSONB(), nullable=False),
        sa.Column("embedding", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # simulation_runs
    op.create_table(
        "simulation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pair_id", sa.String(255), nullable=False, index=True),
        sa.Column(
            "user_a_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id"),
            nullable=False,
        ),
        sa.Column(
            "user_b_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("temporal_workflow_id", sa.String(255), nullable=True),
        sa.Column("n_timelines", sa.Integer(), nullable=False),
        sa.Column("results", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # crisis_episodes
    op.create_table(
        "crisis_episodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "simulation_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("simulation_runs.id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.Float(), nullable=False),
        sa.Column("vulnerability_axis", sa.String(50), nullable=False),
        sa.Column("narrative_elasticity", sa.Float(), nullable=False),
        sa.Column("reached_homeostasis", sa.Boolean(), nullable=False),
        sa.Column("transcript", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # linguistic_profiles
    op.create_table(
        "linguistic_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id"),
            nullable=False,
        ),
        sa.Column("phrase_registry", postgresql.JSONB(), server_default="{}"),
        sa.Column("convergence_history", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "last_simulation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("simulation_runs.id"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("linguistic_profiles")
    op.drop_table("crisis_episodes")
    op.drop_table("simulation_runs")
    op.drop_table("user_profiles")
