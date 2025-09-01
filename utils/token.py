import asyncio
import os
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai.types import HttpOptions, Part
import tiktoken
from vertexai.preview import tokenization

from constants.prompt import REWRITE_SYSTEM_PROMPT
from constants.query import QUERY_HARD_CAP, QUERY_SOFT_CAP, QUERY_TARGET
from services.providers.fpt_llm.client import FPTLLMClient
from utils.packing import count_tokens_total

load_dotenv()

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


# ---------- VOYAGE ----------


def _truncate_to_tokens(text: str, target_tokens: int, api_key: Optional[str] = None) -> str:
    n = count_tokens_total(
        [text], model="voyage-context-3", api_key=api_key or os.getenv("VOYAGEAI_KEY") or ""
    )
    if n <= target_tokens:
        return text
    ratio = max(0.5, target_tokens / max(1, n))
    cut = max(32, int(len(text) * ratio))
    return text[:cut].rstrip()


def _rewrite_sync(client: "FPTLLMClient", query: str, target_tokens: int) -> str:
    if not client.model:
        raise ValueError(
            "FPTLLMClient.model is not set. Pass model=... in __init__ or set client.model before calling _rewrite_sync()."
        )

    messages = [
        {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
        {"role": "user", "content": f"Target length: ~{target_tokens} tokens.\n\nQuery:\n{query}"},
    ]
    resp = client.chat_completions(
        model=client.model,
        messages=messages,
        temperature=0.0,
        top_p=1.0,
        max_tokens=max(32, target_tokens + 16),
        stream=False,
        extra_body=None,
    )

    # Since stream=False, resp should be a Dict[str, Any]
    if not isinstance(resp, dict):
        raise TypeError("Expected dict response when stream=False")

    text = resp["choices"][0]["message"]["content"].strip()
    return text


async def llm_rewrite(
    query: str, *, client: "FPTLLMClient", target_tokens: int = QUERY_TARGET
) -> str:
    rewritten = await asyncio.to_thread(_rewrite_sync, client, query, target_tokens)
    return _truncate_to_tokens(rewritten, target_tokens, api_key=None)


async def normalize_query(q: str, *, client: "FPTLLMClient") -> str:
    api_key = os.getenv("VOYAGEAI_KEY") or ""
    n = count_tokens_total([q], model="voyage-context-3", api_key=api_key)
    if n <= QUERY_SOFT_CAP:
        return q
    if n <= QUERY_HARD_CAP:
        return await llm_rewrite(q, client=client, target_tokens=QUERY_TARGET)
    raise HTTPException(400, detail="Query quá dài; hãy tóm tắt lại tài liệu")
