"""add tree and models relative with raptor

Revision ID: ac396bbf4fbd
Revises: 59178dcb8dca
Create Date: 2025-08-19 08:02:35.618073

"""

from typing import Sequence, Union

from pgvector.sqlalchemy import Vector
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ac396bbf4fbd"
down_revision: Union[str, Sequence[str], None] = "59178dcb8dca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


N_DIM = 1024


def _table_exists(name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return name in insp.get_table_names()


def _index_exists(table: str, index_name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(ix["name"] == index_name for ix in insp.get_indexes(table))


def upgrade() -> None:
    # 0) vector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")  # Postgres-safe

    # 1) enums
    schema = op.get_bind().exec_driver_sql("select current_schema()").scalar() or "public"

    op.execute(f"""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typname = 'raptor_node_kind'
            AND n.nspname = '{schema}'
        ) THEN
            CREATE TYPE "{schema}".raptor_node_kind AS ENUM ('leaf','summary','root');
        END IF;
    END$$;
    """)

    # embedding_owner_type
    op.execute(f"""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typname = 'embedding_owner_type'
            AND n.nspname = '{schema}'
        ) THEN
            CREATE TYPE "{schema}".embedding_owner_type AS ENUM ('chunk','tree_node');
        END IF;
    END$$;
    """)

    raptor_node_kind = postgresql.ENUM(
        "leaf", "summary", "root", name="raptor_node_kind", schema=schema, create_type=False
    )
    embedding_owner_type = postgresql.ENUM(
        "chunk", "tree_node", name="embedding_owner_type", schema=schema, create_type=False
    )

    # 2) trees
    if not _table_exists("trees"):
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
            sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
        )
    if not _index_exists("trees", "ix_trees_dataset"):
        # dùng raw SQL để hỗ trợ IF NOT EXISTS
        op.execute('CREATE INDEX IF NOT EXISTS "ix_trees_dataset" ON trees (dataset_id)')

    # 3) tree_nodes
    if not _table_exists("tree_nodes"):
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
            sa.Column("kind", raptor_node_kind, nullable=False),
            sa.Column("text", sa.Text(), nullable=True),
            sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
        )
    # indexes cho tree_nodes
    op.execute('CREATE INDEX IF NOT EXISTS "ix_tree_nodes_tree" ON tree_nodes (tree_id)')
    op.execute('CREATE INDEX IF NOT EXISTS "ix_tree_nodes_level" ON tree_nodes (level)')
    op.execute(
        'CREATE INDEX IF NOT EXISTS "ix_tree_nodes_tree_level" ON tree_nodes (tree_id, level)'
    )

    # 4) tree_edges
    if not _table_exists("tree_edges"):
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
    op.execute('CREATE INDEX IF NOT EXISTS "ix_tree_edges_parent" ON tree_edges (parent_id)')
    op.execute('CREATE INDEX IF NOT EXISTS "ix_tree_edges_child" ON tree_edges (child_id)')

    # 5) tree_node_chunks
    if not _table_exists("tree_node_chunks"):
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
            sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        )
    op.execute('CREATE INDEX IF NOT EXISTS "ix_node_chunks_node" ON tree_node_chunks (node_id)')
    op.execute('CREATE INDEX IF NOT EXISTS "ix_node_chunks_chunk" ON tree_node_chunks (chunk_id)')

    # 6) embeddings (1024d) + HNSW cosine
    if not _table_exists("embeddings"):
        op.create_table(
            "embeddings",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("dataset_id", sa.String(), nullable=False),
            sa.Column("owner_type", embedding_owner_type, nullable=False),
            sa.Column("owner_id", sa.String(), nullable=False),
            sa.Column("model", sa.String(), nullable=False),
            sa.Column("dim", sa.Integer(), nullable=False, server_default=sa.text(str(N_DIM))),
            sa.Column("v", Vector(N_DIM), nullable=False),
            sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
        )
    if not _index_exists("embeddings", "ix_embeddings_dataset_owner"):
        op.execute(
            'CREATE INDEX IF NOT EXISTS "ix_embeddings_dataset_owner" ON embeddings (dataset_id, owner_type, owner_id)'
        )

    op.execute(
        'CREATE INDEX IF NOT EXISTS "ix_embeddings_v_hnsw" '
        "ON embeddings USING hnsw (v vector_cosine_ops)"
    )


def downgrade() -> None:
    # Xoá index trước (IF EXISTS an toàn trên Postgres 9.5+)
    op.execute('DROP INDEX IF EXISTS "ix_embeddings_v_hnsw"')
    op.execute('DROP INDEX IF EXISTS "ix_embeddings_dataset_owner"')
    if _table_exists("embeddings"):
        op.drop_table("embeddings")

    op.execute('DROP INDEX IF EXISTS "ix_node_chunks_chunk"')
    op.execute('DROP INDEX IF EXISTS "ix_node_chunks_node"')
    if _table_exists("tree_node_chunks"):
        op.drop_table("tree_node_chunks")

    op.execute('DROP INDEX IF EXISTS "ix_tree_edges_child"')
    op.execute('DROP INDEX IF EXISTS "ix_tree_edges_parent"')
    if _table_exists("tree_edges"):
        op.drop_table("tree_edges")

    op.execute('DROP INDEX IF EXISTS "ix_tree_nodes_tree_level"')
    op.execute('DROP INDEX IF EXISTS "ix_tree_nodes_level"')
    op.execute('DROP INDEX IF EXISTS "ix_tree_nodes_tree"')
    if _table_exists("tree_nodes"):
        op.drop_table("tree_nodes")

    op.execute('DROP INDEX IF EXISTS "ix_trees_dataset"')
    if _table_exists("trees"):
        op.drop_table("trees")

    # enums cuối cùng
    op.execute("DROP TYPE IF EXISTS raptor_node_kind")
    op.execute("DROP TYPE IF EXISTS embedding_owner_type")
