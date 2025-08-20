"""add kind enum to tree_nodes

Revision ID: 56cd2b49dff3
Revises: ac396bbf4fbd
Create Date: 2025-08-20 15:40:58.350118

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "56cd2b49dff3"
down_revision: Union[str, Sequence[str], None] = "ac396bbf4fbd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ENUM_NAME = "raptor_node_kind"
ENUM_VALUES = ("leaf", "summary", "root")


def upgrade():
    bind = op.get_bind()

    # 0) (tuỳ chọn) dọn bảng phụ thuộc trước
    for tbl in ("tree_node_chunks", "tree_edges", "tree_nodes", "trees"):
        op.execute(sa.text(f'DROP TABLE IF EXISTS "{tbl}" CASCADE'))

    # 1) (tuỳ chọn) drop type nếu tồn tại, schema-qualified + DO block
    op.execute(
        sa.text(f"""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = '{ENUM_NAME}' AND n.nspname = 'public'
      ) THEN
        DROP TYPE public.{ENUM_NAME};
      END IF;
    END$$;
    """)
    )

    # 2) tạo type MỘT LẦN
    node_kind = pg.ENUM(*ENUM_VALUES, name=ENUM_NAME)
    node_kind.create(bind, checkfirst=True)

    # 3) tạo bảng, cột tham chiếu LẠI type đã có (create_type=False)
    op.create_table(
        "trees",
        sa.Column("tree_id", sa.String(), primary_key=True),
        sa.Column(
            "doc_id",
            sa.String(),
            sa.ForeignKey("documents.doc_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dataset_id", sa.String(), nullable=False),
        sa.Column("params", pg.JSONB()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_trees_dataset", "trees", ["dataset_id"])

    op.create_table(
        "tree_nodes",
        sa.Column("node_id", sa.String(), primary_key=True),
        sa.Column(
            "tree_id",
            sa.String(),
            sa.ForeignKey("trees.tree_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("level", sa.Integer(), nullable=False),
        # CHỐT: dùng ENUM theo tên, KHÔNG tạo lại type
        sa.Column("kind", pg.ENUM(name=ENUM_NAME, create_type=False), nullable=False),
        sa.Column("text", sa.Text()),
        sa.Column("meta", pg.JSONB()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tree_nodes_tree", "tree_nodes", ["tree_id"])
    op.create_index("ix_tree_nodes_level", "tree_nodes", ["level"])
    op.create_index("ix_tree_nodes_kind", "tree_nodes", ["kind"])

    op.create_table(
        "tree_edges",
        sa.Column(
            "parent_id",
            sa.String(),
            sa.ForeignKey("tree_nodes.node_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "child_id",
            sa.String(),
            sa.ForeignKey("tree_nodes.node_id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index("ix_tree_edges_parent", "tree_edges", ["parent_id"])
    op.create_index("ix_tree_edges_child", "tree_edges", ["child_id"])

    op.create_table(
        "tree_node_chunks",
        sa.Column(
            "node_id",
            sa.String(),
            sa.ForeignKey("tree_nodes.node_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "chunk_id",
            sa.String(),
            sa.ForeignKey("chunks.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("rank", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_node_chunks_node", "tree_node_chunks", ["node_id"])
    op.create_index("ix_node_chunks_chunk", "tree_node_chunks", ["chunk_id"])


def downgrade():
    # drop bảng trước, type sau
    for name in ("tree_node_chunks", "tree_edges", "tree_nodes", "trees"):
        op.execute(sa.text(f'DROP TABLE IF EXISTS "{name}" CASCADE'))
    op.execute(sa.text("DROP TYPE IF EXISTS public.raptor_node_kind"))
