"""add seed episode id

Revision ID: 6a166cce52be
Revises: ed1d333e7848
Create Date: 2026-09-05 21:33:49.306882

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6a166cce52be"
down_revision: Union[str, Sequence[str], None] = "ed1d333e7848"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add the column temporarily as nullable.
    op.add_column(
        "episodes",
        sa.Column(
            "seed_episode_id",
            sa.String(length=255),
            nullable=True,
        ),
    )

    # Step 2: Give existing records temporary legacy IDs.
    op.execute(
        """
        UPDATE episodes
        SET seed_episode_id = 'legacy-' || id
        WHERE seed_episode_id IS NULL
        """
    )

    # Step 3: Make the column required.
    op.alter_column(
        "episodes",
        "seed_episode_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    # Step 4: Prevent duplicate seed IDs.
    op.create_index(
        "ix_episodes_seed_episode_id",
        "episodes",
        ["seed_episode_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_episodes_seed_episode_id",
        table_name="episodes",
    )

    op.drop_column(
        "episodes",
        "seed_episode_id",
    )