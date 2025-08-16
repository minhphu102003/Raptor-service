"""add text column in document table

Revision ID: 59178dcb8dca
Revises: 7c8c20d23172
Create Date: 2025-08-15 22:35:28.855011

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "59178dcb8dca"
down_revision: Union[str, Sequence[str], None] = "7c8c20d23172"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add `text` column to `documents`."""
    op.add_column("documents", sa.Column("text", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema: drop `text` column from `documents`."""
    op.drop_column("documents", "text")
