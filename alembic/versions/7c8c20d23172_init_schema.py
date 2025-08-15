"""init schema

Revision ID: 7c8c20d23172
Revises:
Create Date: 2025-08-15 09:32:59.711731
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

from alembic import op

# --- fallback cho Vector nếu pgvector.sqlalchemy không có ---
try:
    from pgvector.sqlalchemy import Vector  # type: ignore
except Exception:  # pragma: no cover

    class Vector(sa.types.UserDefinedType):  # type: ignore
        def __init__(self, dim: int):
            self.dim = dim

        def get_col_spec(self, **kw):
            return f"vector({self.dim})"


# revision identifiers, used by Alembic.
revision: str = "7c8c20d23172"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0) pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 1) documents
    op.create_table(
        "documents",
        sa.Column("doc_id", sa.String(), primary_key=True),
        sa.Column("dataset_id", sa.String(), nullable=False, index=True),
        sa.Column("source", sa.Text()),
        sa.Column("tags", psql.JSONB),
        sa.Column("extra_meta", psql.JSONB),
        sa.Column("checksum", sa.String()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_dataset_id ON documents (dataset_id)")

    # 2) chunks
    op.create_table(
        "chunks",
        sa.Column("id", sa.String(), primary_key=True),  # "{doc_id}:{idx}"
        sa.Column("doc_id", sa.String(), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_cnt", sa.Integer()),
        sa.Column("hash", sa.String()),
        sa.Column("meta", psql.JSONB),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.doc_id"], ondelete="CASCADE"),
    )
    # index & unique như models.py
    op.execute("CREATE INDEX IF NOT EXISTS ix_chunks_doc_idx ON chunks (doc_id, idx)")
    op.create_unique_constraint("uq_chunks_doc_idx", "chunks", ["doc_id", "idx"])

    # 3) vectors (3072)
    op.create_table(
        "vectors",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("ns", sa.Text()),
        sa.Column("v", Vector(3072)),  # cột pgvector
        sa.Column("meta", psql.JSONB),
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_vectors_ns ON vectors (ns)")
    # Chỉ mục HNSW cho cosine (nếu bạn dùng metric cosine). Nếu dùng L2, thay vector_l2_ops.
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vectors_hnsw_cosine
        ON vectors
        USING hnsw ((v::halfvec(3072)) halfvec_cosine_ops);
        """)
    # Nếu muốn L2 thay vì cosine, dùng dòng dưới và xoá dòng trên:
    # op.execute("CREATE INDEX IF NOT EXISTS ix_vectors_hnsw_l2 ON vectors USING hnsw (v vector_l2_ops);")

    # 4) trees
    op.create_table(
        "trees",
        sa.Column("tree_id", sa.String(), primary_key=True),
        sa.Column("doc_id", sa.String(), nullable=False),
        sa.Column("dataset_id", sa.String(), nullable=False),
        sa.Column("params", psql.JSONB),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.doc_id"], ondelete="CASCADE"),
    )

    # 5) tree_nodes
    op.create_table(
        "tree_nodes",
        sa.Column("node_id", sa.String(), primary_key=True),
        sa.Column("tree_id", sa.String(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("meta", psql.JSONB),
        sa.ForeignKeyConstraint(["tree_id"], ["trees.tree_id"], ondelete="CASCADE"),
    )

    # 6) tree_edges
    op.create_table(
        "tree_edges",
        sa.Column("parent_id", sa.String(), primary_key=True),
        sa.Column("child_id", sa.String(), primary_key=True),
        sa.ForeignKeyConstraint(["parent_id"], ["tree_nodes.node_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_id"], ["tree_nodes.node_id"], ondelete="CASCADE"),
    )

    # 7) jobs (tuỳ chọn) – nếu bạn muốn quản lý queue bằng DB
    # op.create_table(
    #     "jobs",
    #     sa.Column("job_id", sa.String(), primary_key=True),
    #     sa.Column("type", sa.String(), nullable=False),
    #     sa.Column("payload", psql.JSONB),
    #     sa.Column("status", sa.String(), nullable=False),  # queued|running|done|failed
    #     sa.Column("error", sa.Text()),
    #     sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    #     sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
    #     sa.Column("finished_at", sa.TIMESTAMP(timezone=True)),
    # )


def downgrade() -> None:
    # Xoá theo thứ tự phụ thuộc ngược
    # Nếu bạn tạo bảng jobs, nhớ drop trước:
    # op.drop_table("jobs")

    op.drop_table("tree_edges")
    op.drop_table("tree_nodes")
    op.drop_table("trees")

    # Drop chỉ mục HNSW nếu cần (không bắt buộc trước khi drop bảng)
    op.execute("DROP INDEX IF EXISTS ix_vectors_hnsw_cosine;")
    # op.execute("DROP INDEX IF EXISTS ix_vectors_hnsw_l2;")
    op.drop_index("ix_vectors_ns", table_name="vectors")
    op.drop_table("vectors")

    op.drop_constraint("uq_chunks_doc_idx", "chunks", type_="unique")
    op.drop_index("ix_chunks_doc_idx", table_name="chunks")
    op.drop_table("chunks")

    op.drop_index("ix_documents_dataset_id", table_name="documents")
    op.drop_table("documents")

    # Extension vector có thể được dùng bởi DB khác, thường không drop extension.
    # Nếu muốn thật sự rollback sạch:
    # op.execute("DROP EXTENSION IF EXISTS vector;")
