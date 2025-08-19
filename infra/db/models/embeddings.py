from __future__ import annotations

from enum import Enum as PyEnum
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import TIMESTAMP, Index, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import N_DIM, Base


class EmbeddingOwnerType(str, PyEnum):
    chunk = "chunk"
    tree_node = "tree_node"


class EmbeddingORM(Base):
    __tablename__ = "embeddings"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String, index=True)
    owner_type: Mapped[EmbeddingOwnerType] = mapped_column(
        SAEnum(EmbeddingOwnerType, name="embedding_owner_type"), index=True
    )
    owner_id: Mapped[str] = mapped_column(String, index=True)
    model: Mapped[str] = mapped_column(String, nullable=False)
    dim: Mapped[int] = mapped_column(Integer, nullable=False, default=N_DIM)
    v: Mapped[list[float]] = mapped_column(Vector(N_DIM), nullable=False)
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        Index("ix_embeddings_dataset_owner", "dataset_id", "owner_type", "owner_id"),
        Index(
            "ix_embeddings_v_hnsw",
            "v",
            postgresql_using="hnsw",
            postgresql_ops={"v": "vector_cosine_ops"},
        ),
    )
