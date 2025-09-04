from typing import Iterable, Sequence

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, bindparam, text
from sqlalchemy.dialects.postgresql import ARRAY


class RetrievalRepo:
    def __init__(self, uow):
        self.session = uow.session

    @staticmethod
    def _vec_param(vec: Sequence[float]) -> list[float]:
        return list(vec)

    async def get_node_metadata(
        self,
        *,
        node_id: str,
    ) -> dict | None:
        """
        Get metadata for a specific tree node.
        """
        sql = text("""
            SELECT
                tn.node_id,
                tn.tree_id,
                tn.level,
                tn.kind,
                tn.text,
                tn.meta,
                t.dataset_id,
                (SELECT COUNT(*) FROM tree_edges te WHERE te.parent_id = tn.node_id) AS children_count,
                (SELECT te.parent_id FROM tree_edges te WHERE te.child_id = tn.node_id LIMIT 1) AS parent_id
            FROM tree_nodes tn
            JOIN trees t ON tn.tree_id = t.tree_id
            WHERE tn.node_id = :node_id
        """)
        res = await self.session.execute(sql, {"node_id": node_id})
        row = res.mappings().first()
        return dict(row) if row else None

    async def get_node_children(
        self,
        *,
        node_id: str,
    ) -> list[dict]:
        """
        Get child nodes for a specific tree node.
        """
        sql = text("""
            SELECT
                tn.node_id,
                tn.tree_id,
                tn.level,
                tn.kind,
                tn.text,
                te.child_id
            FROM tree_edges te
            JOIN tree_nodes tn ON tn.node_id = te.child_id
            WHERE te.parent_id = :node_id
            ORDER BY tn.level, tn.node_id
        """)
        res = await self.session.execute(sql, {"node_id": node_id})
        rows = res.mappings().all()
        return [dict(r) for r in rows]

    async def get_node_parent(
        self,
        *,
        node_id: str,
    ) -> dict | None:
        """
        Get parent node for a specific tree node.
        """
        sql = text("""
            SELECT
                tn.node_id,
                tn.tree_id,
                tn.level,
                tn.kind,
                tn.text
            FROM tree_nodes tn
            JOIN tree_edges te ON tn.node_id = te.parent_id
            WHERE te.child_id = :node_id
            LIMIT 1
        """)
        res = await self.session.execute(sql, {"node_id": node_id})
        row = res.mappings().first()
        return dict(row) if row else None

    async def get_node_siblings(
        self,
        *,
        node_id: str,
    ) -> list[dict]:
        """
        Get sibling nodes for a specific tree node.
        """
        sql = text("""
            SELECT
                tn.node_id,
                tn.tree_id,
                tn.level,
                tn.kind,
                tn.text
            FROM tree_nodes tn
            JOIN tree_edges te ON tn.node_id = te.child_id
            WHERE te.parent_id = (
                SELECT te2.parent_id
                FROM tree_edges te2
                WHERE te2.child_id = :node_id
                LIMIT 1
            )
            AND tn.node_id != :node_id
            ORDER BY tn.level, tn.node_id
        """)
        res = await self.session.execute(sql, {"node_id": node_id})
        rows = res.mappings().all()
        return [dict(r) for r in rows]

    async def get_path_to_root(
        self,
        *,
        node_id: str,
    ) -> list[dict]:
        """
        Get the path from a node to the root of the tree.

        This function traverses up the tree from the given node to the root,
        returning information about each node in the path.
        """
        sql = text("""
            WITH RECURSIVE path_to_root AS (
                -- Base case: start with the given node
                SELECT
                    tn.node_id,
                    tn.tree_id,
                    tn.level,
                    tn.kind,
                    tn.text,
                    0 as depth
                FROM tree_nodes tn
                WHERE tn.node_id = :node_id

                UNION ALL

                -- Recursive case: find parent nodes
                SELECT
                    tn.node_id,
                    tn.tree_id,
                    tn.level,
                    tn.kind,
                    tn.text,
                    ptr.depth + 1
                FROM tree_nodes tn
                JOIN tree_edges te ON tn.node_id = te.parent_id
                JOIN path_to_root ptr ON te.child_id = ptr.node_id
                WHERE ptr.depth < 10  -- Prevent infinite recursion
            )
            SELECT
                node_id,
                tree_id,
                level,
                kind,
                text
            FROM path_to_root
            ORDER BY depth
        """)
        res = await self.session.execute(sql, {"node_id": node_id})
        rows = res.mappings().all()
        return [dict(r) for r in rows]

    async def get_node_texts_by_ids(
        self,
        *,
        node_ids: list[str],
    ) -> list[dict]:
        """
        Get texts for multiple tree nodes by their IDs.

        Args:
            node_ids: List of node IDs to retrieve texts for

        Returns:
            List of dictionaries containing node_id and text
        """
        if not node_ids:
            return []

        sql = text("""
            SELECT
                node_id,
                text
            FROM tree_nodes
            WHERE node_id = ANY(:node_ids)
        """)
        res = await self.session.execute(sql, {"node_ids": node_ids})
        rows = res.mappings().all()
        return [dict(r) for r in rows]

    async def search_summary_nodes(
        self,
        *,
        dataset_id: str,
        q_vec: Sequence[float],
        limit: int,
    ) -> list[dict]:
        """
        Tìm các tree_node (summary/root) gần query nhất.
        """
        sql = text("""
            WITH q AS (SELECT CAST(:q AS vector) AS v)
            SELECT
                tn.node_id, tn.tree_id, tn.level, tn.kind,
                e.v <=> (SELECT v FROM q) AS dist
            FROM embeddings e
            JOIN tree_nodes tn ON tn.node_id = e.owner_id
            WHERE e.dataset_id = :dataset_id
            AND e.owner_type = 'tree_node'
            AND tn.kind IN ('summary','root')
            ORDER BY dist ASC
            LIMIT :limit
        """)
        res = await self.session.execute(
            sql,
            {"dataset_id": dataset_id, "q": self._vec_param(q_vec), "limit": int(limit)},
        )
        rows = res.mappings().all()
        return [dict(r) for r in rows]

    async def gather_leaf_chunks(
        self,
        *,
        dataset_id: str,
        node_ids: Iterable[str],
        q_vec: Sequence[float],
        top_k: int,
    ) -> list[dict]:
        node_ids = list(node_ids)
        if not node_ids:
            return []

        dim = len(q_vec)

        sql = text("""
            WITH cand_chunks AS (
            SELECT DISTINCT tnc.chunk_id
            FROM tree_node_chunks tnc
            WHERE tnc.node_id = ANY(:node_ids)
            )
            SELECT
            c.id  AS chunk_id,
            c.doc_id,
            c.idx,
            c.text,
            e.v <=> :q AS dist
            FROM cand_chunks cc
            JOIN chunks c   ON c.id = cc.chunk_id
            JOIN embeddings e
            ON e.owner_type = 'chunk'
            AND e.owner_id   = c.id
            AND e.dataset_id = :dataset_id
            ORDER BY dist ASC
            LIMIT :top_k
        """).bindparams(
            bindparam("q", type_=Vector(dim)),
            bindparam("node_ids", type_=ARRAY(String())),
        )

        res = await self.session.execute(
            sql,
            {
                "dataset_id": dataset_id,
                "q": list(q_vec),
                "node_ids": node_ids,
                "top_k": int(top_k),
            },
        )
        rows = res.mappings().all()
        return [dict(r) for r in rows]

    async def traversal_retrieve(
        self,
        *,
        dataset_id: str,
        q_vec: Sequence[float],
        top_k: int,
        levels_cap: int,
        per_level_k: int | None = None,
    ) -> list[dict]:
        # 1) root mới nhất
        sql_roots = text("""
            SELECT tn.node_id
            FROM tree_nodes tn
            JOIN trees t ON t.tree_id = tn.tree_id
            WHERE t.dataset_id = :dataset_id
            AND tn.kind = 'root'
            ORDER BY t.created_at DESC
            LIMIT 1
        """)
        r = await self.session.execute(sql_roots, {"dataset_id": dataset_id})
        root = r.scalar()
        if not root:
            return []

        current = [root]
        level = 0
        per_level_k = per_level_k or top_k
        dim = len(q_vec)

        sql_children = text("""
            SELECT
            te.child_id AS node_id,
            tn.level,
            e.v <=> :q AS dist
            FROM tree_edges te
            JOIN tree_nodes tn ON tn.node_id = te.child_id
            JOIN embeddings e
            ON e.owner_type = 'tree_node'
            AND e.owner_id   = tn.node_id
            AND e.dataset_id = :dataset_id
            WHERE te.parent_id = ANY(:parents)
            ORDER BY dist ASC
            LIMIT :k
        """).bindparams(
            bindparam("q", type_=Vector(dim)),
            bindparam("parents", type_=ARRAY(String())),
        )

        while True:
            if levels_cap and level >= levels_cap:
                break
            res = await self.session.execute(
                sql_children,
                {
                    "dataset_id": dataset_id,
                    "q": list(q_vec),
                    "parents": current,
                    "k": int(per_level_k),
                },
            )
            rows = res.mappings().all()
            if not rows:
                break
            current = [row["node_id"] for row in rows]
            level += 1

        return await self.gather_leaf_chunks(
            dataset_id=dataset_id, node_ids=current, q_vec=q_vec, top_k=top_k
        )
