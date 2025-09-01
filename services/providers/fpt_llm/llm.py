from typing import Any, Dict, Iterator, List, Optional

from .client import FPTLLMClient
from .params import ChatCompletionChunk


def simple_chat(
    prompt: str,
    model: str = "Llama-3.3-70B-Instruct",
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 256,
) -> str:
    """
    Convenience helper for single-turn chat.
    """
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})

    client = FPTLLMClient()
    resp = client.chat_completions(
        model=model, messages=msgs, temperature=temperature, max_tokens=max_tokens
    )
    return resp["choices"][0]["message"]["content"]


def stream_chat(
    prompt: str,
    model: str = "Llama-3.3-70B-Instruct",
    system: Optional[str] = None,
    temperature: float = 0.7,
) -> Iterator[ChatCompletionChunk]:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})

    client = FPTLLMClient()
    return client.chat_completions_stream(model=model, messages=msgs, temperature=temperature)
