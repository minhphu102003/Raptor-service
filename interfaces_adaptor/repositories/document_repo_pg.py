from sqlalchemy import insert

from entities.document import Chunk, Document
from infra.db.models import ChunkORM, DocumentORM
from infra.db.session import SessionLocal


class DocumentRepoPg:
    def __init__(self, session_factory=SessionLocal):
        self._Session = session_factory

    def save_document(self, doc: Document) -> None:
        with self._Session() as s:
            try:
                s.merge(
                    DocumentORM(
                        doc_id=doc.doc_id,
                        dataset_id=doc.dataset_id,
                        source=doc.source,
                        tags=doc.tags,
                        extra_meta=doc.extra_meta,
                    )
                )
                if doc.chunks:
                    for c in doc.chunks:
                        s.merge(
                            ChunkORM(
                                id=c.id,
                                doc_id=c.doc_id,
                                idx=c.idx,
                                text=c.text,
                                token_cnt=c.token_cnt,
                                meta=c.meta,
                            )
                        )
                s.commit()
            except Exception:
                s.rollback()
                raise

    def get_document(self, doc_id: str) -> Document | None:
        with self._Session() as s:
            o = s.get(DocumentORM, doc_id)
            if not o:
                return None
            chunks = [
                Chunk(
                    id=c.id,
                    doc_id=c.doc_id,
                    idx=c.idx,
                    text=c.text,
                    token_cnt=c.token_cnt,
                    meta=c.meta,
                )
                for c in o.chunks
            ]
            return Document(
                doc_id=o.doc_id,
                dataset_id=o.dataset_id,
                source=o.source,
                tags=o.tags,
                extra_meta=o.extra_meta,
                chunks=chunks,
            )

    def save_chunks_core(self, chunks: list[dict]) -> None:
        with self._Session() as s:
            try:
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
                s.execute(stmt)
                s.commit()
            except Exception:
                s.rollback()
                raise
