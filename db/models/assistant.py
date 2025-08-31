from __future__ import annotations

from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import TIMESTAMP, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class AssistantStatus(str, PyEnum):
    active = "active"
    inactive = "inactive"
    deleted = "deleted"


class AssistantORM(Base):
    __tablename__ = "assistants"

    assistant_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, index=True)  # For future user management
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Configuration
    knowledge_bases: Mapped[list] = mapped_column(JSONB, nullable=False)  # List of dataset IDs
    model_settings: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Model configuration
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)  # Custom system prompt

    # Status and metadata
    status: Mapped[AssistantStatus] = mapped_column(
        SAEnum(AssistantStatus, name="assistant_status"),
        default=AssistantStatus.active,
        index=True,
    )
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)  # Additional metadata

    # Timestamps
    created_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        """Convert assistant to dictionary representation"""
        return {
            "assistant_id": self.assistant_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "knowledge_bases": self.knowledge_bases,
            "model_settings": self.model_settings,
            "system_prompt": self.system_prompt,
            "status": self.status.value,
            "meta": self.meta,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
