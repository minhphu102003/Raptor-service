import logging
import os
from textwrap import dedent
from typing import Optional, Protocol, Sequence

from dotenv import load_dotenv
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

from services.config import LLMProvider, ModelConfig, get_service_config
from services.providers.fpt_llm.client import ALLOWED_MODELS
from services.shared.exceptions import (
    ContextLimitExceededError,
    LLMError,
    ModelNotSupportedError,
    ValidationError,
)
from utils.token import context_limit_for, count_input_tokens, fits_context

from ..providers.fpt_llm import FPTLLMClient
from ..providers.gemini_chat import GeminiChatLLM

load_dotenv()
glogger = logging.getLogger("gemini")


class ChatLLM(Protocol):
    async def summarize(self, prompt: str, *, max_tokens: int, temperature: float) -> str: ...


class OpenAIChatLLM:
    def __init__(
        self, model: str, api_key: Optional[str] = None, config: Optional[ModelConfig] = None
    ):
        self.model = model
        self.config = config or get_service_config().model_config
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    async def summarize(
        self, prompt: str, *, max_tokens: Optional[int] = None, temperature: Optional[float] = None
    ) -> str:
        # Use config defaults if not provided
        max_tokens = max_tokens or self.config.summarization_max_tokens
        temperature = temperature or self.config.summarization_temperature

        try:
            in_tokens = await count_input_tokens(self.model, prompt=prompt)
            if not fits_context(self.model, in_tokens, max_tokens):
                limit = context_limit_for(self.model)
                raise ContextLimitExceededError(
                    model=self.model, input_tokens=in_tokens, output_tokens=max_tokens, limit=limit
                )

            resp = await self.client.responses.create(
                model=self.model,
                input=prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            return getattr(resp, "output_text", str(resp))

        except Exception as e:
            if isinstance(e, ContextLimitExceededError):
                raise
            raise LLMError(
                f"OpenAI summarization failed for model {self.model}",
                error_code="OPENAI_SUMMARIZATION_FAILED",
                context={"model": self.model, "prompt_length": len(prompt)},
                cause=e,
            )


class LLMSummarizer:
    def __init__(self, chat_llm: ChatLLM, config: Optional[ModelConfig] = None):
        self.llm = chat_llm
        self.config = config or get_service_config().model_config

    async def summarize_cluster(
        self, texts: Sequence[str], max_tokens: Optional[int] = None
    ) -> str:
        if not texts:
            raise ValidationError(
                "Cannot summarize empty text collection",
                error_code="EMPTY_TEXT_COLLECTION",
                context={"texts_count": len(texts)},
            )

        # Use config default if not provided
        max_tokens = max_tokens or self.config.summarization_max_tokens

        try:
            enumerated = "\n\n".join([f"[#{i + 1}] {t}" for i, t in enumerate(texts)])

            prompt = dedent(f"""\
            Summarize the following docs into 4–5 sentences.
            Return PLAIN TEXT ONLY (no labels, no tags, no lists).
            <docs>
            {enumerated}
            </docs>
            """)

            return await self.llm.summarize(
                prompt, max_tokens=max_tokens, temperature=self.config.summarization_temperature
            )

        except Exception as e:
            if isinstance(e, (LLMError, ContextLimitExceededError, ValidationError)):
                raise
            raise LLMError(
                "Cluster summarization failed",
                error_code="CLUSTER_SUMMARIZATION_FAILED",
                context={
                    "texts_count": len(texts),
                    "max_tokens": max_tokens,
                    "total_text_length": sum(len(t) for t in texts),
                },
                cause=e,
            )


def make_llm(model_id: str, config: Optional[ModelConfig] = None) -> ChatLLM:
    """Create LLM instance based on model ID and configuration"""
    if not model_id:
        raise ValidationError("Model ID cannot be empty", error_code="EMPTY_MODEL_ID")

    config = config or get_service_config().model_config

    try:
        # Normalize model name using config
        normalized_model = config.normalize_model_name(model_id)
        provider = config.get_provider(normalized_model)

        if provider == LLMProvider.OPENAI:
            return OpenAIChatLLM(model=normalized_model, config=config)
        elif provider == LLMProvider.GEMINI:
            return GeminiChatLLM(model=normalized_model)
        elif provider == LLMProvider.FPT:
            if normalized_model in ALLOWED_MODELS:
                return FPTLLMClient(model=normalized_model)
            else:
                raise ModelNotSupportedError(normalized_model, list(ALLOWED_MODELS))
        else:
            supported_providers = [p.value for p in LLMProvider]
            raise ModelNotSupportedError(model_id, [f"{p} models" for p in supported_providers])

    except Exception as e:
        if isinstance(e, (ModelNotSupportedError, ValidationError)):
            raise
        raise LLMError(
            f"Failed to create LLM for model {model_id}",
            error_code="LLM_CREATION_FAILED",
            context={"model_id": model_id},
            cause=e,
        )


# Backward compatibility - these constants are now available through config
# But keeping them for any existing code that might import them
def get_model_constants():
    """Get model constants from configuration (backward compatibility)"""
    config = get_service_config().model_config
    return {
        "OPENAI_HIGH": config.get_default_model(LLMProvider.OPENAI),
        "OPENAI_EFFICIENT": "gpt-4o-mini",
        "GEMINI_FAST": config.get_default_model(LLMProvider.GEMINI),
        "DEEPSEEK_V3": config.get_default_model(LLMProvider.FPT),
        "QWEN3_235B": "Qwen3-235B-A22B",
    }


# For backward compatibility
OPENAI_HIGH = "gpt-4o"
OPENAI_EFFICIENT = "gpt-4o-mini"
GEMINI_FAST = "gemini-2.5-flash"
DEEPSEEK_V3 = "DeepSeek-V3"
QWEN3_235B = "Qwen3-235B-A22B"
