"""add_user_profile_clerk_fields

Revision ID: 003
Revises: 002
Create Date: 2026-02-18

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("clerk_user_id", sa.String(255), nullable=True))
    op.add_column("user_profiles", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("user_profiles", sa.Column("name", sa.String(255), nullable=True))
    op.add_column(
        "user_profiles",
        sa.Column("onboarding_complete", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "user_profiles",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.create_index("ix_user_profiles_clerk_user_id", "user_profiles", ["clerk_user_id"], unique=True)
    op.create_index("ix_user_profiles_email", "user_profiles", ["email"])

    op.alter_column("user_profiles", "shadow_vector", server_default="{}")


def downgrade() -> None:
    op.drop_index("ix_user_profiles_email", table_name="user_profiles")
    op.drop_index("ix_user_profiles_clerk_user_id", table_name="user_profiles")
    op.drop_column("user_profiles", "is_deleted")
    op.drop_column("user_profiles", "onboarding_complete")
    op.drop_column("user_profiles", "name")
    op.drop_column("user_profiles", "email")
    op.drop_column("user_profiles", "clerk_user_id")
