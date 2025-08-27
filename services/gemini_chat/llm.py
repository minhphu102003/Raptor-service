import asyncio
from textwrap import dedent
from typing import Any, AsyncIterator, Optional

from google.genai import types
from tenacity import retry, stop_after_attempt, wait_random_exponential

from utils.regex import clean_summary

from .client import make_client
from .errors import EmptyOutputError
from .logging_utils import get_logger
from .params import GenerateParams
from .parser import finish_info, parse_text
from .timer import Timer


class GeminiChatLLM:
    def __init__(self, model: str, client: Optional[Any] = None, logger=None):
        self.model = model
        self.client = client or make_client()
        self.logger = logger or get_logger(__name__)

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    async def summarize(
        self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.2
    ) -> str:
        params = GenerateParams(max_tokens=max_tokens, temperature=temperature)
        pre_tokens = await self._safe_count_tokens(prompt)
        self._log_request(prompt, pre_tokens, params)

        config = self._build_config(params)
        async with Timer() as t:
            resp = await self._safe_generate(prompt, config)

        text = parse_text(resp)
        text = clean_summary(text)
        self._log_usage(resp, t.ms, text)
        self._ensure_non_empty(text, resp, t.ms)
        return text

    async def _safe_count_tokens(self, prompt: str) -> Optional[int]:
        try:
            ct = await self.client.aio.models.count_tokens(model=self.model, contents=prompt)
            return getattr(ct, "total_tokens", None)
        except Exception as e:
            self.logger.debug("count_tokens failed: %r", e)
            return None

    def _log_request(self, prompt: str, pre_tokens: Optional[int], p: GenerateParams) -> None:
        snippet = dedent(prompt)[:600].replace("\n", " ")
        self.logger.info(
            "[Gemini] model=%s pre_tokens=%s max_out=%s temp=%.2f prompt[0:600]='%s...'",
            self.model,
            pre_tokens,
            p.max_tokens,
            p.temperature,
            snippet,
        )

    def _build_config(self, p: GenerateParams) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            temperature=p.temperature,
            max_output_tokens=p.max_tokens,
            response_mime_type=p.mime,
            candidate_count=p.candidates,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=p.disable_afc),
            thinking_config=types.ThinkingConfig(thinking_budget=p.thinking_budget),
        )

    async def _generate(self, prompt: str, config: types.GenerateContentConfig) -> Any:
        return await self.client.aio.models.generate_content(
            model=self.model, contents=prompt, config=config
        )

    def _ensure_non_empty(self, text: str, resp: Any, latency_ms: float) -> None:
        fr, pf = finish_info(resp)
        if text and text.strip():
            self.logger.info(
                "[Gemini] finish_reason=%s output_chars=%d latency_ms=%.1f",
                fr,
                len(text),
                latency_ms,
            )
            self.logger.info("[Gemini] output_preview='%s...'", text.replace("\n", " "))
        else:
            self.logger.error(
                "[Gemini] empty output | finish_reason=%s | prompt_feedback=%s | latency_ms=%.1f",
                fr,
                pf,
                latency_ms,
            )
            raise EmptyOutputError(
                f"Gemini returned empty text (finish_reason={fr}, prompt_feedback={pf})."
            )

    def _log_usage(self, resp: Any, latency_ms: float, text: str) -> None:
        um = getattr(resp, "usage_metadata", None)
        if um:
            self.logger.info(
                "[Gemini] usage prompt=%s candidates=%s total=%s",
                getattr(um, "prompt_token_count", None),
                getattr(um, "candidates_token_count", None),
                getattr(um, "total_token_count", None),
            )

    async def _safe_generate(self, prompt: str, config: types.GenerateContentConfig) -> Any:
        async with Timer() as t:
            resp = await self._generate(prompt, config)

        min_interval = 6.2
        if t.ms < min_interval * 1000:
            wait_time = min_interval - (t.ms / 1000)
            await asyncio.sleep(wait_time)

        return resp

    async def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 4000,
        temperature: float = 0.3,
        clean: bool = False,
    ) -> str:
        """
        Non-stream: trả full text, dùng lại pipeline log + _safe_generate hiện có.
        """
        params = GenerateParams(max_tokens=max_tokens, temperature=temperature)
        pre_tokens = await self._safe_count_tokens(prompt)
        self._log_request(prompt, pre_tokens, params)

        config = self._build_config(params)
        async with Timer() as t:
            resp = await self._safe_generate(prompt, config)

        text = parse_text(resp)  # bạn đã có parser thống nhất
        if clean:
            text = clean_summary(text)

        self._log_usage(resp, t.ms, text)
        self._ensure_non_empty(text, resp, t.ms)
        return text

    async def astream(
        self,
        prompt: str,
        *,
        max_tokens: int = 4000,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        """
        Stream: yield từng mẩu text khi model sinh ra (SSE của google-genai).
        """
        params = GenerateParams(max_tokens=max_tokens, temperature=temperature)
        pre_tokens = await self._safe_count_tokens(prompt)
        self._log_request(prompt, pre_tokens, params)

        cfg = self._build_config(params)

        try:
            async for chunk in self.client.aio.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config=cfg,
            ):
                text_piece = getattr(chunk, "text", None)
                if text_piece:
                    yield text_piece
        finally:
            pass
