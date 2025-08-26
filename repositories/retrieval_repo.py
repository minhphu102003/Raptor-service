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
