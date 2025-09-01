from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from typing import Optional

from langchain_openai import ChatOpenAI


@dataclass(frozen=True)
class OpenAIChatConfig:
    model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
    timeout: int = int(os.getenv("OPENAI_TIMEOUT", "60"))
    max_retries: int = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
    api_key: Optional[str] = None
    base_url: Optional[str] = os.getenv("OPENAI_BASE_URL") or None


def _build_llm(cfg: OpenAIChatConfig) -> ChatOpenAI:
    """
    Tạo ChatOpenAI theo cấu hình. Cho phép BYOK (api_key, base_url).
    """
    kwargs = dict(
        model=cfg.model,
        temperature=cfg.temperature,
        timeout=cfg.timeout,
        max_retries=cfg.max_retries,
    )
    if cfg.api_key:
        kwargs["api_key"] = cfg.api_key
    if cfg.base_url:
        kwargs["base_url"] = cfg.base_url
    return ChatOpenAI(**kwargs)


@lru_cache(maxsize=32)
def get_chat_llm(
    model: Optional[str] = None,
    *,
    temperature: float = 0.0,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
) -> ChatOpenAI:
    """
    Factory có cache: với cùng (model, temperature, base_url, api_key-id) sẽ tái sử dụng instance.
    Tránh lãng phí kết nối và cho phép truyền BYOK theo request khi cần.
    """
    # để cache không làm lộ API key, chỉ dùng “id” thô thiển: 8 ký tự đầu
    api_key_id = (api_key or os.getenv("OPENAI_API_KEY") or "")[:8]
    cfg = OpenAIChatConfig(
        model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=temperature,
        timeout=int(timeout or os.getenv("OPENAI_TIMEOUT", "60")),
        max_retries=int(max_retries or os.getenv("OPENAI_MAX_RETRIES", "3")),
        api_key=api_key or os.getenv("OPENAI_API_KEY"),
        base_url=base_url or os.getenv("OPENAI_BASE_URL") or None,
    )
    # để cache phân biệt theo key-id & base_url
    cache_key = (cfg.model, cfg.temperature, cfg.timeout, cfg.max_retries, api_key_id, cfg.base_url)

    # trick: lru_cache bọc trên hàm; muốn lợi dụng cache_key -> tạo inner
    def _make(key):
        return _build_llm(cfg)

    return _make(cache_key)


# tiện ích chuyên cho “edge smoothing” (nhiệt độ=0)
def get_edge_decider_llm(
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> ChatOpenAI:
    return get_chat_llm(
        model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.0,
        api_key=api_key,
        base_url=base_url,
    )
