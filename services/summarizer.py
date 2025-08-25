import logging
import os
from textwrap import dedent
from typing import Optional, Protocol, Sequence

from dotenv import load_dotenv
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

from services.fpt_llm.client import ALLOWED_MODELS
from utils.token import context_limit_for, count_input_tokens, fits_context

from .fpt_llm import FPTLLMClient
from .gemini_chat import GeminiChatLLM

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
        self, prompt: str, *, max_tokens: int = 512, temperature: float = 0.2
    ) -> str:
        in_tokens = await count_input_tokens(self.model, prompt=prompt)
        if not fits_context(self.model, in_tokens, max_tokens):
            limit = context_limit_for(self.model)
            raise ValueError(
                f"Input ({in_tokens}) + output ({max_tokens}) exceeds context limit "
                f"({limit}) for model '{self.model}'. Consider map-reduce or upgrade model."
            )
        resp = await self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        return getattr(resp, "output_text", str(resp))


class LLMSummarizer:
    def __init__(self, chat_llm: ChatLLM):
        self.llm = chat_llm

    async def summarize_cluster(self, texts: Sequence[str], max_tokens: int = 8000) -> str:
        enumerated = "\n\n".join([f"[#{i + 1}] {t}" for i, t in enumerate(texts)])

        prompt = dedent(f"""\
        Summarize the docs below.
        **Keep output under 450 tokens.**
        Output EXACTLY these sections:
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
DEEPSEEK_V3 = "DeepSeek-V3"
QWEN3_235B = "Qwen3-235B-A22B"


def make_llm(model_id: str) -> ChatLLM:
    mid = model_id.lower()
    if mid.startswith("gpt-") or mid.startswith("o"):
        return OpenAIChatLLM(model=model_id)
    if mid.startswith("gemini"):
        return GeminiChatLLM(model=model_id)
    if model_id in ALLOWED_MODELS:
        return FPTLLMClient(model=model_id)
    raise ValueError(f"Unsupported model id: {model_id}")
