from __future__ import annotations

from typing import Any, List, Optional

from sqlalchemy import TIMESTAMP, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class DocumentORM(Base):
    __tablename__ = "documents"
    doc_id: Mapped[str] = mapped_column(String, primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[Any]] = mapped_column(JSONB)
    extra_meta: Mapped[Optional[dict]] = mapped_column(JSONB)
    checksum: Mapped[Optional[str]] = mapped_column(String)
    text: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    chunks: Mapped[List["ChunkORM"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class ChunkORM(Base):
    __tablename__ = "chunks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    doc_id: Mapped[str] = mapped_column(
        String, ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_cnt: Mapped[Optional[int]] = mapped_column(Integer)
    hash: Mapped[Optional[str]] = mapped_column(String)
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)
    document: Mapped[DocumentORM] = relationship(back_populates="chunks", lazy="joined")
    __table_args__ = (
        Index("ix_chunks_doc_idx", "doc_id", "idx"),
        UniqueConstraint("doc_id", "idx", name="uq_chunks_doc_idx"),
    )
