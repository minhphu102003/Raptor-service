import psycopg

from interfaces_adaptor.ports import IVectorIndex


class PgVectorIndex(IVectorIndex):
    def __init__(self, engine, dim: int):
        self.engine = engine
        self.table = sa.Table("chunk_embeddings_d1024", metadata, autoload_with=engine)

    async def bulk_upsert(self, *, dim, model, method, items):
        rows = [
            {"chunk_id": cid, "model": model, "method": method, "dim": dim, "embedding": vec}
            for cid, vec in items
        ]
        stmt = (
            pg_insert(self.table)
            .values(rows)
            .on_conflict_do_update(
                index_elements=[self.table.c.chunk_id],
                set_={
                    "embedding": sa.text("excluded.embedding"),
                    "model": sa.text("excluded.model"),
                    "method": sa.text("excluded.method"),
                },
            )
        )
        async with self.engine.begin() as conn:
            await conn.execute(stmt)
        return len(rows)
