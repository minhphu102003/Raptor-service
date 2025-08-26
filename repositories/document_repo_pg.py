from typing import Optional

from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from db.models import ChunkORM, DocumentORM
from interfaces_adaptor.ports import IDocumentRepository, IUnitOfWork


class DocumentRepoPg(IDocumentRepository):
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def save_document(self, doc: dict) -> None:
        s = self.uow.session

        s.add(DocumentORM(**doc))

    async def get_document(self, doc_id: str) -> Optional[dict]:
        s = self.uow.session
        stmt = (
            select(DocumentORM)
            .options(selectinload(DocumentORM.chunks))
            .where(DocumentORM.doc_id == doc_id)
        )
        res = await s.execute(stmt)
        o = res.scalars().first()
        if not o:
            return None
        return {
            "doc_id": o.doc_id,
            "dataset_id": o.dataset_id,
            "source": o.source,
            "tags": o.tags,
            "extra_meta": o.extra_meta,
            "chunks": [
                {
                    "id": c.id,
                    "doc_id": c.doc_id,
                    "idx": c.idx,
                    "text": c.text,
                    "token_cnt": c.token_cnt,
                    "meta": c.meta,
                }
                for c in o.chunks
            ],
        }

    async def find_by_checksum(self, dataset_id: str, checksum: str) -> Optional[DocumentORM]:
        s = self.uow.session
        stmt = select(DocumentORM).where(
            DocumentORM.dataset_id == dataset_id, DocumentORM.checksum == checksum
        )
        res = await s.execute(stmt)
        return res.scalars().first()

    async def save_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        s = self.uow.session
        stmt = insert(ChunkORM).values(chunks)
        stmt = stmt.on_conflict_do_update(
            index_elements=[ChunkORM.id],
            set_={
                "text": stmt.excluded.text,
                "token_cnt": stmt.excluded.token_cnt,
                "meta": stmt.excluded.meta,
                "idx": stmt.excluded.idx,
                "doc_id": stmt.excluded.doc_id,
            },
        )
        await s.execute(stmt)

    # async def dataset_exists(self, dataset_id: str) -> bool:
    #     s = self.uow.session
    #     stmt = select(exists().where(DocumentORM.dataset_id == dataset_id))
    #     return (await s.execute(stmt)).scalar()
