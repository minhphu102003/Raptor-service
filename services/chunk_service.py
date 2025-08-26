from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.chunk_repo_pg import ChunkRepoPg


class ChunkService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ChunkRepoPg(session)

    async def store_chunks(
        self,
        *,
        doc_id: str,
        dataset_id: str,
        chunk_texts: List[str],
        source_uri: Optional[str] = None,
        extra_meta: Optional[Dict[str, Any]] = None,
        ids: Optional[List[str]] = None,
        start_index: int = 0,
        token_counts: Optional[List[Optional[int]]] = None,
        hashes: Optional[List[Optional[str]]] = None,
    ) -> List[str]:
        n = len(chunk_texts)
        ids = ids or [f"{doc_id}::c{i + start_index}" for i in range(n)]
        toks = token_counts or [None] * n
        hshs = hashes or [None] * n
        meta_base = extra_meta or {}

        rows = []
        for i, (cid, txt, tok, hv) in enumerate(zip(ids, chunk_texts, toks, hshs)):
            rows.append(
                {
                    "id": cid,
                    "doc_id": doc_id,
                    "idx": i + start_index,
                    "text": txt,
                    "token_cnt": tok,
                    "hash": hv,
                    "meta": {"source_uri": source_uri, **meta_base},
                }
            )

        await self.repo.bulk_upsert(rows)
        return ids
