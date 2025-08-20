import logging
import os
from typing import List, Sequence

from dotenv import load_dotenv

from utils.packing import count_tokens_total

load_dotenv()

api_key = os.getenv("VOYAGEAI_KEY")
logger = logging.getLogger("voyage")


class VoyageEmbedderAdapter:
    def __init__(self, cce):
        self.cce = cce
        self.model_name = cce.model
        self.dim = cce.out_dim
        self.api_key = cce.api_key or api_key

    async def embed_docs(self, texts: Sequence[str]) -> List[List[float]]:
        batches, cur, cur_tok = [], [], 0
        for t in texts:
            t_tok = count_tokens_total(
                texts=[t], model="voyage-context-3", api_key=self.cce.api_key
            )
            if cur and (cur_tok + t_tok > self.cce.per_request_token_budget or len(cur) >= 1000):
                batches.append(cur)
                cur, cur_tok = [], 0
            cur.append(t)
            cur_tok += t_tok
        if cur:
            batches.append(cur)
        out = []
        for batch in batches:
            inputs = [[t] for t in batch]
            tok = self.cce.vo.count_tokens(batch)
            await self.cce.limiter.acquire(tok)
            resp = await self.cce.vo.contextualized_embed(
                inputs=inputs,
                model=self.model_name,
                input_type="document",
                output_dimension=self.cce.out_dim,
                output_dtype=self.cce.out_dtype,
            )
            for r in resp.results:
                out.append(r.embeddings[0])
        return out
