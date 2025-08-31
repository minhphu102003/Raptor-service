"""add chat table

Revision ID: 5d6c602f7c75
Revises: 56cd2b49dff3
Create Date: 2025-08-30 09:58:19.404401

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5d6c602f7c75"
down_revision: Union[str, Sequence[str], None] = "56cd2b49dff3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types with proper existence check
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'chat_session_status') THEN
                CREATE TYPE chat_session_status AS ENUM ('active', 'archived', 'deleted');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_role') THEN
                CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
            END IF;
        END $$;
    """)

    # Create chat_sessions table
    op.create_table(
        "chat_sessions",
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("dataset_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active", "archived", "deleted", name="chat_session_status", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("assistant_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=True),
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
        sa.PrimaryKeyConstraint("session_id", name=op.f("pk_chat_sessions")),
    )
    op.create_index("ix_chat_sessions_dataset_id", "chat_sessions", ["dataset_id"], unique=False)
    op.create_index("ix_chat_sessions_status", "chat_sessions", ["status"], unique=False)
    op.create_index(
        "ix_chat_sessions_status_created", "chat_sessions", ["status", "created_at"], unique=False
    )
    op.create_index(
        "ix_chat_sessions_user_dataset", "chat_sessions", ["user_id", "dataset_id"], unique=False
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"], unique=False)

    # Create chat_messages table
    op.create_table(
        "chat_messages",
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("user", "assistant", "system", name="message_role", create_type=False),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context_passages", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("retrieval_query", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(), nullable=True),
        sa.Column("generation_params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.session_id"],
            name=op.f("fk_chat_messages_session_id_chat_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("message_id", name=op.f("pk_chat_messages")),
    )
    op.create_index("ix_chat_messages_role", "chat_messages", ["role"], unique=False)
    op.create_index(
        "ix_chat_messages_session_created",
        "chat_messages",
        ["session_id", "created_at"],
        unique=False,
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"], unique=False)

    # Create chat_context table
    op.create_table(
        "chat_context",
        sa.Column("context_id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("context_messages", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("context_size_tokens", sa.Integer(), nullable=False),
        sa.Column("max_context_tokens", sa.Integer(), nullable=True),
        sa.Column("summarized_history", sa.Text(), nullable=True),
        sa.Column("last_message_id", sa.String(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.session_id"],
            name=op.f("fk_chat_context_session_id_chat_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("context_id", name=op.f("pk_chat_context")),
    )
    op.create_index("ix_chat_context_session", "chat_context", ["session_id"], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_table("chat_context")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")

    # Drop enum types if they exist
    op.execute("DROP TYPE IF EXISTS message_role CASCADE")
    op.execute("DROP TYPE IF EXISTS chat_session_status CASCADE")
