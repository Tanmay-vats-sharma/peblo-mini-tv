"""improve artwork storage metadata

Revision ID: 8f7cf5f7515d
Revises: 87f5889f6d76
Create Date: 2026-09-05

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f7cf5f7515d"
down_revision: Union[str, Sequence[str], None] = "87f5889f6d76"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new metadata columns.
    op.add_column(
        "artworks",
        sa.Column(
            "original_filename",
            sa.String(length=255),
            nullable=False,
            server_default="legacy-artwork",
        ),
    )

    op.add_column(
        "artworks",
        sa.Column(
            "storage_key",
            sa.String(length=1000),
            nullable=False,
            server_default="legacy-storage-key",
        ),
    )

    op.add_column(
        "artworks",
        sa.Column(
            "mime_type",
            sa.String(length=100),
            nullable=False,
            server_default="image/jpeg",
        ),
    )

    # Existing artwork rows were temporary placeholders.
    # Remove the temporary defaults after the columns exist.
    op.alter_column(
        "artworks",
        "original_filename",
        server_default=None,
    )

    op.alter_column(
        "artworks",
        "storage_key",
        server_default=None,
    )

    op.alter_column(
        "artworks",
        "mime_type",
        server_default=None,
    )

    # image_url is now optional because storage_key is the primary
    # storage reference.
    op.alter_column(
        "artworks",
        "image_url",
        existing_type=sa.String(length=1000),
        nullable=True,
    )

    # These fields must always contain actual image metadata.
    op.alter_column(
        "artworks",
        "width",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "artworks",
        "height",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "artworks",
        "file_size_bytes",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # Keep the existing PostgreSQL enum type artwork_type.
    # Do not try to rename or recreate it.
    op.create_unique_constraint(
        "uq_artworks_show_type",
        "artworks",
        ["show_id", "artwork_type"],
    )

    op.create_unique_constraint(
        "uq_artworks_storage_key",
        "artworks",
        ["storage_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_artworks_storage_key",
        "artworks",
        type_="unique",
    )

    op.drop_constraint(
        "uq_artworks_show_type",
        "artworks",
        type_="unique",
    )

    op.drop_column("artworks", "mime_type")
    op.drop_column("artworks", "storage_key")
    op.drop_column("artworks", "original_filename")