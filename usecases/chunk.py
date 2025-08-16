from typing import Any, Dict, List

import tiktoken

from interfaces_adaptor.ports import IDocumentRepository

from .types import NaiveChunkConfig


class ChunkDocumentNaiveUseCase:
    def __init__(self, *, doc_repo: IDocumentRepository):
        self.doc_repo = doc_repo

    def _encode(self, text: str, enc_name: str):
        enc = tiktoken.get_encoding(enc_name)
        return enc, enc.encode(text)

    def _decode(self, token_ids: list[int], enc):
        return enc.decode(token_ids)

    def _sliding_windows(self, tokens: list[int], size: int, overlap: int):
        overlap = max(0, min(overlap, size - 1))
        step = size - overlap
        i = 0
        while i < len(tokens):
            yield i, tokens[i : i + size]
            if len(tokens) <= size:
                break
            i += step
            if i <= 0:
                i = 1

    async def execute(
        self,
        *,
        doc_id: str,
        text: str,
        cfg: NaiveChunkConfig,
        base_meta: Dict[str, Any] | None = None,
    ) -> dict:
        """
        Trả về {"doc_id":..., "n_chunks":..., "saved": ...}
        Lưu theo schema ChunkORM(id, doc_id, idx, text, token_cnt, meta)
        """
        enc, token_ids = self._encode(text, cfg.tokenizer_encoding)

        chunks_to_save: List[dict] = []
        idx = 0
        for start, win in self._sliding_windows(
            token_ids, cfg.chunk_size_tokens, cfg.chunk_overlap_tokens
        ):
            chunk_text = self._decode(win, enc)
            chunk_meta = {
                **(base_meta or {}),
                "start_token": start,
                "end_token": start + len(win) - 1,
                "method": "naive",
                "chunk_size_tokens": cfg.chunk_size_tokens,
                "chunk_overlap_tokens": cfg.chunk_overlap_tokens,
            }
            chunks_to_save.append(
                {
                    "id": f"{doc_id}:{idx}",
                    "doc_id": doc_id,
                    "idx": idx,
                    "text": chunk_text,
                    "token_cnt": len(win),
                    "meta": chunk_meta,
                }
            )
            idx += 1
            if cfg.max_chunks is not None and idx >= cfg.max_chunks:
                break

        await self.doc_repo.save_chunks(chunks_to_save)
        return {"doc_id": doc_id, "n_chunks": len(chunks_to_save), "saved": True}
