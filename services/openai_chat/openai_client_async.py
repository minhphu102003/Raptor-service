from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator, Optional

from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError


class OpenAIClientAsync:
    """
    Client OpenAI (Responses API) tương thích AnswerService:
      - generate(): trả full string
      - astream(): yield từng delta text để StreamingResponse đẩy về client
    """

    def __init__(
        self,
        *,
        model: str = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        request_timeout: float = 60.0,
        max_concurrent: int = 4,
    ) -> None:
        self.model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("Missing OPENAI_API_KEY")

        self.client = AsyncOpenAI(api_key=key, base_url=base_url or None)
        self.request_timeout = request_timeout
        self._sem = asyncio.Semaphore(max(1, int(max_concurrent)))

    # ---- public API khớp với AnswerService ----
    async def generate(self, *, prompt: str, temperature: float, max_tokens: int) -> str:
        """
        Gọi non-stream qua Responses API và trả text đã ghép.
        """
        async with self._sem:
            try:
                resp = await self.client.responses.create(
                    model=self.model_name,
                    input=prompt,
                    temperature=temperature,
                    # map: AnswerService.max_tokens -> Responses.max_output_tokens
                    max_output_tokens=max_tokens,
                    timeout=self.request_timeout,
                )
            except (RateLimitError, APITimeoutError, APIError) as e:
                raise

            return getattr(resp, "output_text", "") or ""

    async def astream(
        self, *, prompt: str, temperature: float, max_tokens: int
    ) -> AsyncIterator[str]:
        """
        Streaming qua Responses API (SSE). Yield từng delta text.
        """
        async with self._sem:
            try:
                async with self.client.responses.stream(
                    model=self.model_name,
                    input=prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    timeout=self.request_timeout,
                ) as stream:
                    async for event in stream:
                        if getattr(event, "type", "") == "response.output_text.delta":
                            delta = getattr(event, "delta", None)
                            if delta:
                                yield delta
            except (RateLimitError, APITimeoutError, APIError) as e:
                raise

    @property
    def model(self) -> str:
        return self.model_name
