"""
fpt_llm
-------
Lightweight client for FPT AI Marketplace LLM endpoints.

Quick start:

    from fpt_llm import FPTLLMClient

    client = FPTLLMClient()  # reads FPT_MKP_API_KEY / FPT_MKP_BASE_URL from env
    resp = client.chat_completions(
        model="Llama-3.3-70B-Instruct",
        messages=[{"role": "user", "content": "Xin chào, giới thiệu ngắn về bạn"}],
        max_tokens=256,
        temperature=0.7,
    )
    print(resp["choices"][0]["message"]["content"])

Streaming:

    for chunk in client.chat_completions_stream(
        model="Llama-3.3-70B-Instruct",
        messages=[{"role": "user", "content": "Viết 1 đoạn văn 3 câu về Trà Vinh"}],
        temperature=0.7,
    ):
        if chunk.delta:
            print(chunk.delta, end="", flush=True)

Environment variables:
- FPT_MKP_API_KEY:   Your API key from marketplace.fptcloud.com
- FPT_MKP_BASE_URL:  Base URL (default: https://mkp-api.fptcloud.com)

See: https://github.com/fpt-corp/ai-marketplace (API uses Authorization: Bearer <API_KEY> and /v1/chat/completions)
"""

from .client import FPTLLMClient
from .errors import (
    APIError,
    AuthenticationError,
    FPTLLMError,
    RateLimitError,
)
from .params import ChatCompletionChunk, ChatMessage

__all__ = [
    "FPTLLMClient",
    "APIError",
    "AuthenticationError",
    "FPTLLMError",
    "RateLimitError",
    "ChatCompletionChunk",
    "ChatMessage",
]
