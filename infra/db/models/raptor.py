from __future__ import annotations

from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import TIMESTAMP, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class NodeKind(str, PyEnum):
    leaf = "leaf"
    summary = "summary"
    root = "root"


class TreeORM(Base):
    __tablename__ = "trees"
    tree_id: Mapped[str] = mapped_column(String, primary_key=True)
    doc_id: Mapped[str] = mapped_column(
        String, ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False
    )
    dataset_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    params: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    nodes: Mapped[List["TreeNodeORM"]] = relationship(
        back_populates="tree", cascade="all, delete-orphan", passive_deletes=True
    )


class TreeNodeORM(Base):
    __tablename__ = "tree_nodes"
    node_id: Mapped[str] = mapped_column(String, primary_key=True)
    tree_id: Mapped[str] = mapped_column(
        String, ForeignKey("trees.tree_id", ondelete="CASCADE"), nullable=False, index=True
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    kind: Mapped[NodeKind] = mapped_column(
        SAEnum(*[e.value for e in NodeKind], name="raptor_node_kind"), index=True
    )
    text: Mapped[Optional[str]] = mapped_column(Text)
    meta: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[str]] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    tree: Mapped["TreeORM"] = relationship(back_populates="nodes")


class TreeEdgeORM(Base):
    __tablename__ = "tree_edges"
    parent_id: Mapped[str] = mapped_column(
        String, ForeignKey("tree_nodes.node_id", ondelete="CASCADE"), primary_key=True
    )
    child_id: Mapped[str] = mapped_column(
        String, ForeignKey("tree_nodes.node_id", ondelete="CASCADE"), primary_key=True
    )
    __table_args__ = (
        Index("ix_tree_edges_parent", "parent_id"),
        Index("ix_tree_edges_child", "child_id"),
    )


class TreeNodeChunkORM(Base):
    __tablename__ = "tree_node_chunks"
    node_id: Mapped[str] = mapped_column(
        String, ForeignKey("tree_nodes.node_id", ondelete="CASCADE"), primary_key=True
    )
    chunk_id: Mapped[str] = mapped_column(
        String, ForeignKey("chunks.id", ondelete="CASCADE"), primary_key=True
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    __table_args__ = (
        Index("ix_node_chunks_node", "node_id"),
        Index("ix_node_chunks_chunk", "chunk_id"),
    )
