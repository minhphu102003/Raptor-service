import asyncio
import json
import os
import threading
import time
from typing import Any, Dict, Iterator, List, Optional, Union

import requests

from utils.http import parse_retry_after

from .errors import APIError, AuthenticationError, RateLimitError
from .logging_utils import get_logger
from .params import DEFAULT_BASE_URL, ChatCompletionChunk
from .throttle import BackoffPolicy, RateLimiter

log = get_logger("fpt_llm.client")

ALLOWED_MODELS = {"DeepSeek-V3", "Qwen3-235B-A22B"}


class FPTLLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        session: Optional[requests.Session] = None,
        rpm: Optional[int] = None,
        min_interval: Optional[float] = None,
        max_retries: int = 5,
        backoff_base: float = 0.5,
        backoff_max: float = 20.0,
        backoff_jitter: float = 0.25,
        max_concurrent: int = 4,
        *,
        model: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("FPT_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "Missing API key. Set FPT_MKP_API_KEY (or FPT_API_KEY) or pass api_key=..."
            )

        self.base_url = base_url or os.getenv("FPT_MKP_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

        self._limiter = RateLimiter(rpm=rpm, min_interval=min_interval)
        self._backoff = BackoffPolicy(
            max_retries=max_retries,
            base_delay=backoff_base,
            max_delay=backoff_max,
            jitter=backoff_jitter,
        )
        self.model = model
        self._sem = threading.BoundedSemaphore(value=max(1, int(max_concurrent)))

    def chat_completions(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        extra_body: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], Iterator[ChatCompletionChunk]]:
        self._validate_model(model)
        payload: Dict[str, Any] = {"model": model, "messages": messages}
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if extra_body:
            payload.update(extra_body)

        url = f"{self.base_url}/v1/chat/completions"
        headers = self._headers()

        if not stream:
            return self._call_with_throttle(
                lambda: self.session.post(url, headers=headers, json=payload, timeout=self.timeout),
                expect_stream=False,
            )
        else:
            payload["stream"] = True
            return self._call_with_throttle(
                lambda: self.session.post(
                    url, headers=headers, json=payload, timeout=self.timeout, stream=True
                ),
                expect_stream=True,
            )

    async def summarize(self, prompt: str, *, max_tokens: int, temperature: float) -> str:
        if not self.model:
            raise ValueError(
                "FPTLLMClient.model is not set. Pass model=... in __init__ or set client.model before calling summarize()."
            )
        messages = [
            {"role": "system", "content": "You are a concise, faithful summarizer."},
            {"role": "user", "content": prompt},
        ]

        def _request_once() -> Dict[str, Any]:
            return self.chat_completions(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )

        resp: Dict[str, Any] = await asyncio.to_thread(_request_once)

        try:
            choices = resp.get("choices") or []
            if not choices:
                raise KeyError("Missing 'choices' in response")

            first = choices[0]
            content = None

            if isinstance(first, dict) and isinstance(first.get("message"), dict):
                content = first["message"].get("content")

            if content is None and "text" in first:
                content = first["text"]

            if isinstance(content, list):
                parts = []
                for p in content:
                    if isinstance(p, dict):
                        if p.get("type") == "text" and "text" in p:
                            parts.append(p["text"])
                        elif "content" in p:
                            parts.append(str(p["content"]))
                    elif isinstance(p, str):
                        parts.append(p)
                content = "".join(parts).strip()

            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty content extracted from completion")

            if content.lower().startswith("summary:"):
                content = content[len("summary:") :].strip()

            return content

        except Exception as e:
            log.exception("Failed to parse chat completion response: %s", e)
            payload_keys = list(resp.keys()) if isinstance(resp, dict) else type(resp).__name__
            raise RuntimeError(f"Bad completion payload ({payload_keys}): {e}") from e

    def _validate_model(self, model: str):
        if model not in ALLOWED_MODELS:
            raise APIError(f"Model '{model}' không nằm trong whitelist: {sorted(ALLOWED_MODELS)}")

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _call_with_throttle(self, request_fn, expect_stream: bool):
        attempt = 0
        while True:
            attempt += 1
            self._limiter.acquire()
            with self._sem:
                resp = request_fn()

            if resp.status_code == 401 or resp.status_code == 403:
                raise AuthenticationError(f"Auth failed ({resp.status_code}): {resp.text}")
            if resp.status_code == 429:
                retry_after = parse_retry_after(resp)
                if attempt > self._backoff.max_retries:
                    raise RateLimitError(
                        f"Rate limited after {attempt - 1} retries: {resp.text}",
                        status_code=429,
                        retry_after=retry_after,
                    )
                time.sleep(self._backoff.compute_sleep(attempt, retry_after))
                continue
            if resp.status_code >= 500:
                if attempt > self._backoff.max_retries:
                    raise APIError(
                        f"Server error after {attempt - 1} retries ({resp.status_code}): {resp.text}",
                        status_code=resp.status_code,
                    )
                time.sleep(self._backoff.compute_sleep(attempt, None))
                continue

            if not expect_stream:
                return self._handle_json_response(resp)
            else:
                return self._stream_chat_chunks(resp)

    def _handle_json_response(self, resp: requests.Response) -> Dict[str, Any]:
        try:
            return resp.json()
        except Exception as e:
            raise APIError(f"Invalid JSON response: {e}; body={resp.text[:1000]}")

    def _stream_chat_chunks(self, resp: requests.Response) -> Iterator[ChatCompletionChunk]:
        from .parser import parse_sse_lines

        for data in parse_sse_lines(resp.iter_lines()):
            try:
                payload = json.loads(data)
            except Exception:
                from .params import ChatCompletionChunk

                yield ChatCompletionChunk(
                    id=None, created=None, model=None, delta=data, raw={"raw": data}
                )
                continue
            delta_text = ""
            try:
                choices = payload.get("choices", [])
                if choices:
                    delta_text = (choices[0].get("delta", {}) or {}).get("content", "") or ""
            except Exception:
                pass

            from .params import ChatCompletionChunk

            yield ChatCompletionChunk(
                id=payload.get("id"),
                created=payload.get("created"),
                model=payload.get("model"),
                delta=delta_text,
                raw=payload,
            )
