from __future__ import annotations

from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .assistant import AssistantORM  # Import AssistantORM
from .base import Base


class ChatSessionStatus(str, PyEnum):
    active = "active"
    archived = "archived"
    deleted = "deleted"


class MessageRole(str, PyEnum):
    user = "user"
    assistant = "assistant"
    system = "system"


class ChatSessionORM(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, index=True)  # For future user management
    assistant_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("assistants.assistant_id"), index=True
    )  # Link to assistant
    dataset_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ChatSessionStatus] = mapped_column(
        SAEnum(ChatSessionStatus, name="chat_session_status"),
        default=ChatSessionStatus.active,
        index=True,
    )

    # Assistant configuration (kept for backward compatibility)
    assistant_config: Mapped[Optional[dict]] = mapped_column(JSONB)  # Model, temperature, etc.
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)

    # Metadata
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    messages: Mapped[List["ChatMessageORM"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )
    # Relationship to Assistant
    assistant: Mapped[Optional[AssistantORM]] = relationship(
        "AssistantORM", foreign_keys=[assistant_id]
    )

    __table_args__ = (
        Index("ix_chat_sessions_user_dataset", "user_id", "dataset_id"),
        Index("ix_chat_sessions_status_created", "status", "created_at"),
    )


class ChatMessageORM(Base):
    __tablename__ = "chat_messages"

    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False
    )

    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, name="message_role"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Context and retrieval information
    context_passages: Mapped[Optional[list]] = mapped_column(JSONB)  # Retrieved passages
    retrieval_query: Mapped[Optional[str]] = mapped_column(Text)  # Original or rewritten query
    model_used: Mapped[Optional[str]] = mapped_column(String)  # Which model generated this

    # Generation parameters
    generation_params: Mapped[Optional[dict]] = mapped_column(JSONB)  # temp, top_k, etc.

    # Metadata
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    # Relationships
    session: Mapped[ChatSessionORM] = relationship(back_populates="messages", lazy="joined")

    __table_args__ = (
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
        Index("ix_chat_messages_role", "role"),
    )


class ChatContextORM(Base):
    __tablename__ = "chat_context"

    context_id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False
    )

    # Context window management
    context_messages: Mapped[list] = mapped_column(
        JSONB, nullable=False
    )  # Simplified message history
    context_size_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    max_context_tokens: Mapped[int] = mapped_column(Integer, default=4000)

    # Context optimization
    summarized_history: Mapped[Optional[str]] = mapped_column(Text)  # Compressed old context
    last_message_id: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_chat_context_session", "session_id"),)
