from typing import Iterable

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.models import EmbeddingORM


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
