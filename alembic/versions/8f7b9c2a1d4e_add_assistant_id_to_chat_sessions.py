"""add assistant_id to chat_sessions table

Revision ID: 8f7b9c2a1d4e
Revises: f1a2b3c4d5e6
Create Date: 2025-09-01 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f7b9c2a1d4e"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add assistant_id column to chat_sessions table
    op.add_column("chat_sessions", sa.Column("assistant_id", sa.String(), nullable=True))

    # Create index for assistant_id
    op.create_index(
        "ix_chat_sessions_assistant_id", "chat_sessions", ["assistant_id"], unique=False
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_chat_sessions_assistant_id",
        "chat_sessions",
        "assistants",
        ["assistant_id"],
        ["assistant_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint("fk_chat_sessions_assistant_id", "chat_sessions", type_="foreignkey")

    # Drop index
    op.drop_index("ix_chat_sessions_assistant_id", table_name="chat_sessions")

    # Drop column
    op.drop_column("chat_sessions", "assistant_id")
