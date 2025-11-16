"""Add no_data_ranges table.

Revision ID: d1e2f3a4b5c6
Revises: cb321cf565bf
Create Date: 2025-11-16 04:55:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "cb321cf565bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "no_data_ranges",
        sa.Column("security_id", sa.Integer(), nullable=False),
        sa.Column("start_timestamp", sa.BigInteger(), nullable=False),
        sa.Column("end_timestamp", sa.BigInteger(), nullable=False),
        sa.Column("last_checked", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["security_id"],
            ["securities.id"],
        ),
        sa.PrimaryKeyConstraint("security_id", "start_timestamp", "end_timestamp"),
    )
    op.create_index("idx_no_data_ranges_security", "no_data_ranges", ["security_id"], unique=False)
    op.create_index(
        "idx_no_data_ranges_timestamps",
        "no_data_ranges",
        ["security_id", "start_timestamp", "end_timestamp"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_no_data_ranges_timestamps", table_name="no_data_ranges")
    op.drop_index("idx_no_data_ranges_security", table_name="no_data_ranges")
    op.drop_table("no_data_ranges")
