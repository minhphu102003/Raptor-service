"""add assistant table

Revision ID: f1a2b3c4d5e6
Revises: 5d6c602f7c75
Create Date: 2025-08-31 10:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "5d6c602f7c75"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create assistant_status enum type
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'assistant_status') THEN
                CREATE TYPE assistant_status AS ENUM ('active', 'inactive', 'deleted');
            END IF;
        END $$;
    """)

    # Create assistants table
    op.create_table(
        "assistants",
        sa.Column("assistant_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("knowledge_bases", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model_settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active", "inactive", "deleted", name="assistant_status", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("assistant_id", name=op.f("pk_assistants")),
    )

    # Create indexes
    op.create_index("ix_assistants_user_id", "assistants", ["user_id"], unique=False)
    op.create_index("ix_assistants_status", "assistants", ["status"], unique=False)


def downgrade() -> None:
    # Drop table
    op.drop_table("assistants")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS assistant_status CASCADE")
