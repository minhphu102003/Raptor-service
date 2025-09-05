import asyncio
import os
from typing import Optional

from fastapi import HTTPException

from constants.prompt import REWRITE_SYSTEM_PROMPT
from constants.query import QUERY_HARD_CAP, QUERY_SOFT_CAP, QUERY_TARGET
from utils.packing import count_tokens_total


class QueryRewriteService:
    def __init__(self, fpt_client):
        self.fpt = fpt_client

    def _rewrite_sync(self, query: str, target_tokens: int) -> str:
        """Gọi đồng bộ client FPT (requests) — sẽ chạy trong threadpool qua asyncio.to_thread()."""
        model_name = self.fpt.model or "DeepSeek-V3"
        messages = [
            {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Target length: ~{target_tokens} tokens.\n\nQuery:\n{query}",
            },
        ]
        resp = self.fpt.chat_completions(
            model=model_name,
            messages=messages,
            temperature=0.0,
            top_p=1.0,
            max_tokens=max(32, target_tokens + 16),
            stream=False,
            extra_body=None,
        )
        return resp["choices"][0]["message"]["content"].strip()

    async def _rewrite(
        self,
        query: str,
        *,
        target_tokens: int = QUERY_TARGET,
    ) -> str:
        """Async wrapper cho _rewrite_sync + truncate theo token."""
        rewritten = await asyncio.to_thread(self._rewrite_sync, query, target_tokens)
        return rewritten

    # ---------- public API ----------
    async def normalize_query(
        self,
        q: str,
        *,
        byok_voyage_key: Optional[str] = None,
        soft_cap: int = QUERY_SOFT_CAP,
        hard_cap: int = QUERY_HARD_CAP,
        target_tokens: int = QUERY_TARGET,
    ) -> str:
        if not q or not q.strip():
            raise HTTPException(400, detail="Query rỗng.")

        tok_key = byok_voyage_key or os.getenv("VOYAGEAI_KEY")

        n = count_tokens_total([q], model="voyage-context-3", api_key=tok_key or "")
        if n <= soft_cap:
            return q
        if n <= hard_cap:
            return await self._rewrite(q, target_tokens=target_tokens)
        raise HTTPException(400, detail="Query quá dài; hãy tóm tắt hoặc upload làm tài liệu.")
