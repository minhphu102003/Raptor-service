from typing import Iterable, List, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EmbeddingORM
from db.models.embeddings import EmbeddingOwnerType


class EmbeddingRepoPg:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_upsert(self, rows: Iterable[dict]) -> int:
        rows = list(rows)
        if not rows:
            return 0

        insert_stmt = pg_insert(EmbeddingORM.__table__).values(rows)

        stmt = insert_stmt.on_conflict_do_update(
            index_elements=[EmbeddingORM.__table__.c.id],
            set_={
                "dataset_id": insert_stmt.excluded.dataset_id,
                "owner_type": insert_stmt.excluded.owner_type,
                "owner_id": insert_stmt.excluded.owner_id,
                "model": insert_stmt.excluded.model,
                "dim": insert_stmt.excluded.dim,
                "v": insert_stmt.excluded.v,
                "meta": insert_stmt.excluded.meta,
            },
        )
        await self.session.execute(stmt)
        return len(rows)

    async def list_owner_vectors_by_dataset(
        self,
        dataset_id: str,
        *,
        owner_type: EmbeddingOwnerType = EmbeddingOwnerType.chunk,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Tuple[str, list[float]]]:
        stmt = select(EmbeddingORM.owner_id, EmbeddingORM.v).where(
            EmbeddingORM.dataset_id == dataset_id,
            EmbeddingORM.owner_type == owner_type,
        )
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)

        res = await self.session.execute(stmt)
        return res.all()

    async def delete_by_tree_id(
        self,
        tree_id: str,
        *,
        dataset_id: Optional[str] = None,
        owner_type: Optional[EmbeddingOwnerType] = None,
    ) -> List[str]:
        conds = [EmbeddingORM.meta.contains({"tree_id": tree_id})]
        if dataset_id is not None:
            conds.append(EmbeddingORM.dataset_id == dataset_id)
        if owner_type is not None:
            conds.append(EmbeddingORM.owner_type == owner_type)

        stmt = sa.delete(EmbeddingORM).where(sa.and_(*conds)).returning(EmbeddingORM.id)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def delete_by_tree_ids(
        self,
        tree_ids: Iterable[str],
        *,
        dataset_id: Optional[str] = None,
        owner_type: Optional[EmbeddingOwnerType] = None,
    ) -> List[str]:
        tree_ids = list(tree_ids)
        if not tree_ids:
            return []

        conds = [EmbeddingORM.meta["tree_id"].astext.in_(tree_ids)]
        if dataset_id is not None:
            conds.append(EmbeddingORM.dataset_id == dataset_id)
        if owner_type is not None:
            conds.append(EmbeddingORM.owner_type == owner_type)

        stmt = sa.delete(EmbeddingORM).where(sa.and_(*conds)).returning(EmbeddingORM.id)
        res = await self.session.execute(stmt)
        return res.scalars().all()
