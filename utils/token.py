import os
from typing import Literal, Optional

from google import genai
from google.genai.types import HttpOptions, Part
import tiktoken
from vertexai.preview import tokenization

ModelVendor = Literal["openai", "gemini"]

CONTEXT_LIMITS = {
    "gpt-4.1": 1_000_000,
    "gpt-4.1-mini": 1_000_000,
    "gpt-4o": 128_000,
    "gemini-2.5-pro": 1_048_576,
    "gemini-2.5-flash": 1_048_576,
}


def norm_model_key(model_id: str) -> str:
    return model_id.lower().strip()


def context_limit_for(model_id: str, default: int = 128_000) -> int:
    key = norm_model_key(model_id)
    if key.startswith("gpt-4.1-mini"):
        key = "gpt-4.1-mini"
    elif key.startswith("gpt-4.1"):
        key = "gpt-4.1"
    elif key.startswith("gpt-4o"):
        key = "gpt-4o"
    elif key.startswith("gemini-2.5-pro"):
        key = "gemini-2.5-pro"
    elif key.startswith("gemini-2.5-flash"):
        key = "gemini-2.5-flash"
    return CONTEXT_LIMITS.get(key, default)


# ---------- OPENAI ----------
def count_tokens_openai(text: str, model: str) -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))


# ---------- GEMINI ----------
def count_tokens_gemini_local(text: str, model_name: str) -> int:
    tok = tokenization.get_tokenizer_for_model(model_name)
    return tok.count_tokens(text).total_tokens


def count_tokens_gemini_api(text: str, model: str, api_key: Optional[str] = None) -> int:
    client = genai.Client(
        api_key=api_key or os.getenv("GEMINI_API_KEY"), http_options=HttpOptions(api_version="v1")
    )
    resp = client.models.count_tokens(model=model, contents=[Part(text=text)])
    return getattr(resp, "total_tokens", 0)


def vendor_of(model_id: str) -> ModelVendor:
    mid = model_id.lower()
    if mid.startswith(("gpt-", "o", "gpt")):
        return "openai"
    if mid.startswith("gemini"):
        return "gemini"
    raise ValueError(f"Unknown vendor for model: {model_id}")


async def count_input_tokens(model_id: str, prompt: str) -> int:
    v = vendor_of(model_id)
    if v == "openai":
        return count_tokens_openai(prompt, model_id)
    try:
        return count_tokens_gemini_api(prompt, model_id)
    except Exception:
        return count_tokens_gemini_local(prompt, model_id)


def fits_context(
    model_id: str, input_tokens: int, max_output_tokens: int, safety_margin: int = 768
) -> bool:
    limit = context_limit_for(model_id)
    return (input_tokens + max_output_tokens + safety_margin) <= limit
