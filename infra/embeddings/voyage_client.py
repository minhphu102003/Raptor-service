from typing import Callable, List, Optional, Tuple

import voyageai
from voyageai.error import APIConnectionError, APIError, RateLimitError

from utils.packing import count_tokens_total, token_lengths
from utils.ratelimit import RateLimiter


class VoyageEmbeddingClientAsync:
    def __init__(
        self,
        api_key: str,
        model: str = "voyage-context-3",
        out_dim: int = 1024,
        out_dtype: str = "float",
        rpm_limit: int = 3,
        tpm_limit: int = 10_000,
        max_retries: int = 3,
        per_request_token_budget: int = 9_500,
    ):
        self.api_key = api_key
        self.vo = voyageai.AsyncClient(api_key=api_key, max_retries=max_retries)
        self.model = model
        self.out_dim = out_dim
        self.out_dtype = out_dtype
        self.limiter = RateLimiter(rpm=rpm_limit, tpm=tpm_limit)
        self.per_request_token_budget = per_request_token_budget

    def _pack_groups_by_tpm(self, chunks: List[str]) -> List[List[str]]:
        lens = token_lengths(chunks, self.model, self.api_key)
        groups, cur, used = [], [], 0
        for ch, n in zip(chunks, lens):
            if n > self.per_request_token_budget:
                if cur:
                    groups.append(cur)
                    cur, used = [], 0
                groups.append([ch])
                continue
            if used + n > self.per_request_token_budget and cur:
                groups.append(cur)
                cur, used = [], 0
            cur.append(ch)
            used += n
        if cur:
            groups.append(cur)
        return groups

    async def embed_doc_fulltext_rate_limited(
        self,
        text: str,
        *,
        chunk_fn: Optional[Callable[[str], List[str]]] = None,
    ) -> Tuple[List[List[float]], List[str]]:
        chunks = chunk_fn(text) if chunk_fn else [text]
        groups = self._pack_groups_by_tpm(chunks)
        print("DEBUG ***** 2 : ")
        all_embeddings, all_chunks = [], []
        for group in groups:
            group_tokens = count_tokens_total(group, self.model, self.api_key)
            await self.limiter.acquire(group_tokens)
            print("DEBUG ***** 3 : ")
            try:
                resp = await self.vo.contextualized_embed(
                    inputs=[group],
                    model=self.model,
                    input_type="document",
                    output_dimension=self.out_dim,
                    output_dtype=self.out_dtype,
                )
            except (RateLimitError, APIConnectionError, APIError):
                raise

            r0 = resp.results[0]
            all_embeddings.extend(r0.embeddings)
            all_chunks.extend(group)
        print("DEBUG ***** 4 : ")
        return all_embeddings, all_chunks

    async def embed_queries(self, queries: List[str]) -> List[List[float]]:
        r = await self.vo.contextualized_embed(
            inputs=[[q] for q in queries],
            model=self.model,
            input_type="query",
            output_dimension=self.out_dim,
            output_dtype=self.out_dtype,
        )
        return [res.embeddings[0] for res in r.results]
