from typing import Iterable

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ChunkORM


class ChunkRepoPg:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_upsert(self, rows: Iterable[dict]) -> int:
        rows = list(rows)
        if not rows:
            return 0

        insert_stmt = pg_insert(ChunkORM.__table__).values(rows)

        update_cols = {
            "text": insert_stmt.excluded.text,
            "token_cnt": insert_stmt.excluded.token_cnt,
            "hash": insert_stmt.excluded.hash,
            "meta": insert_stmt.excluded.meta,
        }

        stmt = insert_stmt.on_conflict_do_update(
            index_elements=[ChunkORM.__table__.c.id],
            set_=update_cols,
        )
        await self.session.execute(stmt)
        return len(rows)
