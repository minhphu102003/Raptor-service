from typing import Iterable, List, Tuple

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import TreeEdgeORM, TreeNodeChunkORM, TreeNodeORM, TreeORM


class TreeRepoPg:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tree(self, *, doc_id: str, dataset_id: str, params: dict | None) -> str:
        tree_id = f"{doc_id}::tree"
        stmt = (
            pg_insert(TreeORM.__table__)
            .values(tree_id=tree_id, doc_id=doc_id, dataset_id=dataset_id, params=params or {})
            .on_conflict_do_nothing(index_elements=[TreeORM.__table__.c.tree_id])
        )
        await self.session.execute(stmt)
        return tree_id

    async def add_nodes(self, tree_id: str, rows: Iterable[dict]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        stmt = (
            pg_insert(TreeNodeORM.__table__)
            .values(rows)
            .on_conflict_do_nothing(index_elements=[TreeNodeORM.__table__.c.node_id])
        )
        await self.session.execute(stmt)
        return len(rows)

    async def add_edges(self, tree_id: str, rows: Iterable[dict]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        stmt = pg_insert(TreeEdgeORM.__table__).values(rows).on_conflict_do_nothing()
        await self.session.execute(stmt)
        return len(rows)

    async def link_node_chunks(self, rows: Iterable[dict]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        stmt = pg_insert(TreeNodeChunkORM.__table__).values(rows).on_conflict_do_nothing()
        await self.session.execute(stmt)
        return len(rows)

    async def get_node_texts(self, node_ids: List[str]) -> List[Tuple[str, str]]:
        q = sa.select(TreeNodeORM.node_id, TreeNodeORM.text).where(
            TreeNodeORM.node_id.in_(node_ids)
        )
        res = await self.session.execute(q)
        return [(r[0], r[1]) for r in res.all()]
