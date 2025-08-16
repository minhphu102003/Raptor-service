# infrastructure/db/models.py
from __future__ import annotations

from typing import Any, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    TIMESTAMP,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# ---------- Base with naming convention (Alembic-friendly) ----------
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# ---------- Documents & Chunks ----------
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
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ChunkORM(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    doc_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_cnt: Mapped[Optional[int]] = mapped_column(Integer)
    hash: Mapped[Optional[str]] = mapped_column(String)
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)

    document: Mapped[DocumentORM] = relationship(
        back_populates="chunks",
        lazy="joined",
    )

    __table_args__ = (
        Index("ix_chunks_doc_idx", "doc_id", "idx"),
        UniqueConstraint("doc_id", "idx", name="uq_chunks_doc_idx"),
    )


# ---------- Vectors (pgvector) ----------
# Nếu bạn cần đa chiều (1536 + 3072), hãy tạo thêm bảng vectors_1536 và
# chọn bảng theo embedder.dim trong gateway. Ở đây minh hoạ một bảng 3072.
class Vector3072ORM(Base):
    __tablename__ = "vectors"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    ns: Mapped[Optional[str]] = mapped_column(Text)
    v: Mapped[list[float]] = mapped_column(Vector(3072))
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)

    __table_args__ = (
        Index("ix_vectors_ns", "ns"),
        # Chỉ mục HNSW/IVF phải tạo thủ công trong migration (op.execute(...))
    )


# ---------- RAPTOR Trees ----------
class TreeORM(Base):
    __tablename__ = "trees"

    tree_id: Mapped[str] = mapped_column(String, primary_key=True)
    doc_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
    )
    dataset_id: Mapped[str] = mapped_column(String, nullable=False)
    params: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    nodes: Mapped[List["TreeNodeORM"]] = relationship(
        back_populates="tree",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class TreeNodeORM(Base):
    __tablename__ = "tree_nodes"

    node_id: Mapped[str] = mapped_column(String, primary_key=True)
    tree_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("trees.tree_id", ondelete="CASCADE"),
        nullable=False,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)

    tree: Mapped[TreeORM] = relationship(back_populates="nodes")


class TreeEdgeORM(Base):
    __tablename__ = "tree_edges"

    parent_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("tree_nodes.node_id", ondelete="CASCADE"),
        primary_key=True,
    )
    child_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("tree_nodes.node_id", ondelete="CASCADE"),
        primary_key=True,
    )
