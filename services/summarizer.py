import logging
import os
from textwrap import dedent
import time
from typing import Optional, Protocol, Sequence

from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

load_dotenv()
glogger = logging.getLogger("gemini")


class ChatLLM(Protocol):
    async def summarize(self, prompt: str, *, max_tokens: int, temperature: float) -> str: ...


class OpenAIChatLLM:
    def __init__(self, model: str, api_key: Optional[str] = None):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    async def summarize(
        self, prompt: str, *, max_tokens: int = 256, temperature: float = 0.2
    ) -> str:
        resp = await self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        return getattr(resp, "output_text", str(resp))


class GeminiChatLLM:
    def __init__(self, model: str, client: Optional[genai.Client] = None):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = model
        self.client = client or genai.Client(api_key=api_key)

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    async def summarize(
        self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.2
    ) -> str:
        try:
            ct = await self.client.aio.models.count_tokens(model=self.model, contents=prompt)
            pre_tokens = getattr(ct, "total_tokens", None)
        except Exception as e:
            pre_tokens = None
            glogger.debug("count_tokens failed: %r", e)

        snippet = dedent(prompt)[:600].replace("\n", " ")
        glogger.info(
            "[Gemini] model=%s pre_tokens=%s max_out=%s temp=%.2f prompt[0:600]='%s...'",
            self.model,
            pre_tokens,
            max_tokens,
            temperature,
            snippet,
        )

        t0 = time.perf_counter()
        resp = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="text/plain",
                candidate_count=1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                thinking_config=types.ThinkingConfig(thinking_budget=64),
            ),
        )
        latency_ms = (time.perf_counter() - t0) * 1e3

        um = getattr(resp, "usage_metadata", None)
        if um:
            glogger.info(
                "[Gemini] usage prompt=%s candidates=%s total=%s",
                getattr(um, "prompt_token_count", None),
                getattr(um, "candidates_token_count", None),
                getattr(um, "total_token_count", None),
            )

        out_text = getattr(resp, "text", None)
        if not out_text:
            try:
                d = resp.to_dict()
                for c in d.get("candidates") or []:
                    parts = (c.get("content") or {}).get("parts") or []
                    texts = [p.get("text") for p in parts if isinstance(p, dict) and p.get("text")]
                    if texts:
                        out_text = "\n".join(texts)
                        break
            except Exception:
                out_text = None

        fr = None
        pf = None
        try:
            cand0 = (resp.candidates or [None])[0]
            fr = getattr(cand0, "finish_reason", None)
            pf = getattr(resp, "prompt_feedback", None)
        except Exception:
            pass

        if not out_text or not out_text.strip():
            glogger.error(
                "[Gemini] empty output | finish_reason=%s | prompt_feedback=%s | latency_ms=%.1f",
                fr,
                pf,
                latency_ms,
            )
            raise RuntimeError(
                f"Gemini returned empty text (finish_reason={fr}, prompt_feedback={pf})."
            )

        glogger.info(
            "[Gemini] finish_reason=%s output_chars=%d latency_ms=%.1f",
            fr,
            len(out_text),
            latency_ms,
        )
        glogger.info("[Gemini] output_preview='%s...'", out_text[:300].replace("\n", " "))
        return out_text


class LLMSummarizer:
    def __init__(self, chat_llm: ChatLLM):
        self.llm = chat_llm

    async def summarize_cluster(self, texts: Sequence[str], max_tokens: int = 512) -> str:
        enumerated = "\n\n".join([f"[#{i + 1}] {t}" for i, t in enumerate(texts[:64])])

        prompt = dedent(f"""\
        Summarize the docs below. Output EXACTLY these sections:
        Summary: 3–4 sentences.
        Key facts: 3–6 bullets.
        Entities: comma list.
        Topics: 3–6 tags.
        Evidence: [#i,...]
        Uncertainties: bullets or "None".
        Rules: Use only <docs>; keep entities/numbers/dates; note contradictions; if unsure say "unknown".
        <docs>
        {enumerated}
        </docs>
        """)

        return await self.llm.summarize(prompt, max_tokens=max_tokens, temperature=0.2)


OPENAI_HIGH = "gpt-4.1"
OPENAI_EFFICIENT = "gpt-4.1-mini"
GEMINI_FAST = "gemini-2.5-flash"


def make_llm(model_id: str) -> ChatLLM:
    mid = model_id.lower()
    if mid.startswith("gpt-") or mid.startswith("o"):
        return OpenAIChatLLM(model=model_id)
    if mid.startswith("gemini"):
        return GeminiChatLLM(model=model_id)
    raise ValueError(f"Unsupported model id: {model_id}")
