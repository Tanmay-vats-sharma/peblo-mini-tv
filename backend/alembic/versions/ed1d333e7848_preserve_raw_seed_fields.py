"""preserve raw seed fields

Revision ID: ed1d333e7848
Revises: fb9c85df2ae0
Create Date: 2026-09-05 21:20:58.792694

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "ed1d333e7848"
down_revision: Union[str, Sequence[str], None] = "fb9c85df2ae0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add the new columns with temporary server defaults so that
    # existing rows, if any, receive valid values.
    op.add_column(
        "episodes",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="draft",
        ),
    )

    op.add_column(
        "shows",
        sa.Column(
            "categories",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )

    # Convert PostgreSQL enum values to their string representation.
    op.execute(
        """
        ALTER TABLE episodes
        ALTER COLUMN language TYPE VARCHAR(10)
        USING lower(language::text)
        """
    )

    op.execute(
        """
        ALTER TABLE shows
        ALTER COLUMN section TYPE VARCHAR(50)
        USING lower(section::text)
        """
    )

    op.alter_column(
        "shows",
        "section",
        existing_type=sa.String(length=50),
        nullable=True,
    )

    op.create_index(
        op.f("ix_episodes_status"),
        "episodes",
        ["status"],
        unique=False,
    )

    # The defaults are only needed during migration.
    # Application-level defaults are already defined in the models.
    op.alter_column(
        "episodes",
        "status",
        server_default=None,
    )

    op.alter_column(
        "shows",
        "categories",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Convert strings back to PostgreSQL enums.
    op.execute(
        """
        ALTER TABLE shows
        ALTER COLUMN section TYPE show_section
        USING upper(section)::show_section
        """
    )

    op.execute(
        """
        ALTER TABLE episodes
        ALTER COLUMN language TYPE episode_language
        USING upper(language)::episode_language
        """
    )

    op.alter_column(
        "shows",
        "section",
        existing_type=postgresql.ENUM(
            "FEATURED",
            "SERIES",
            "MINISODES",
            "SONGS",
            name="show_section",
        ),
        nullable=False,
    )

    op.drop_column("shows", "categories")

    op.drop_index(
        op.f("ix_episodes_status"),
        table_name="episodes",
    )

    op.drop_column("episodes", "status")