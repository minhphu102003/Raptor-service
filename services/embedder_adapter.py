import asyncio
import logging
from typing import List, Sequence

from utils.packing import count_tokens_total

logger = logging.getLogger("voyage")


class VoyageEmbedderAdapter:
    """
    Adapter nhận một instance VoyageEmbeddingClientAsync (cce) có:
      - cce.slots: List[_ClientSlot(key, client, limiter, sem)]
      - cce.model, cce.out_dim, cce.out_dtype
      - cce.per_request_token_budget, cce.max_retries
    Mục tiêu: embed nhiều "docs" (mỗi text là 1 doc) càng nhanh càng tốt.
    """

    def __init__(self, cce):
        self.cce = cce
        self.model_name = cce.model
        self.dim = cce.out_dim
        self.api_key = cce.slots[0].key
        self._rr = 0

    def _pick_slot(self):
        slot = self.cce.slots[self._rr % len(self.cce.slots)]
        self._rr += 1
        return slot

    def _make_batches(self, texts: Sequence[str]) -> List[List[str]]:
        """Chia thành batches theo per_request_token_budget (và hạn mức item/req)."""
        batches, cur, cur_tok = [], [], 0
        BATCH_MAX_ITEMS = 2000
        for t in texts:
            t_tok = count_tokens_total([t], model=self.model_name, api_key=self.api_key)
            if cur and (
                cur_tok + t_tok > self.cce.per_request_token_budget or len(cur) >= BATCH_MAX_ITEMS
            ):
                batches.append(cur)
                cur, cur_tok = [], 0
            cur.append(t)
            cur_tok += t_tok
        if cur:
            batches.append(cur)
        return batches

    async def _embed_batch_on_slot(self, batch_idx: int, batch: List[str]):
        """
        Chạy 1 batch trên 1 slot:
          - đếm token đúng model+key của slot
          - limiter.acquire
          - call contextualized_embed(inputs=[[doc], [doc], ...])
          - retry/backoff nhẹ nếu 429/5xx
        """
        slot = self._pick_slot()
        tok = count_tokens_total(batch, model=self.model_name, api_key=slot.key)
        attempt = 0
        backoff = 0.5

        async with slot.sem:
            await slot.limiter.acquire(tok)

            while True:
                try:
                    resp = await slot.client.contextualized_embed(
                        inputs=[[t] for t in batch],
                        model=self.model_name,
                        input_type="document",
                        output_dimension=self.cce.out_dim,
                        output_dtype=self.cce.out_dtype,
                    )

                    embs = [r.embeddings[0] for r in resp.results]
                    return batch_idx, embs
                except Exception as e:
                    attempt += 1
                    if attempt > self.cce.max_retries:
                        logger.exception("[Voyage] batch %d failed after retries", batch_idx)
                        raise
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 8.0)
                    logger.warning(
                        "[Voyage] retry batch %d attempt=%d err=%s", batch_idx, attempt, e
                    )

    async def embed_docs(self, texts: Sequence[str]) -> List[List[float]]:
        """
        Trả về embeddings theo đúng thứ tự input.
        Dùng fan-out qua nhiều slot nếu có >1 batch.
        """
        batches = self._make_batches(texts)

        if len(batches) == 1:
            _, embs = await self._embed_batch_on_slot(0, batches[0])
            return embs

        tasks = [self._embed_batch_on_slot(i, b) for i, b in enumerate(batches)]
        results = await asyncio.gather(*tasks)

        results.sort(key=lambda x: x[0])
        out: List[List[float]] = []
        for _, embs in results:
            out.extend(embs)
        return out
