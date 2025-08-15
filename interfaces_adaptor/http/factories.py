from app.config import settings
from interfaces_adaptor.gateways.embedder_openai import OpenAIEmbedder

from ..model_ref import parse_model_ref

# TODO: thêm HF/Cohere/Dashscope/Gemini...


def make_embedder(
    embedding_model: str,
    space: str,
    normalized: bool,
    byok: dict | None,
    target_dim: int | None = None,
):
    ref = parse_model_ref(embedding_model)
    factory = (ref.factory or "openai").lower()
    if factory == "openai":
        key = (byok or {}).get("openai_api_key") or settings.openai_api_key
        if not key:
            raise ValueError("Missing OpenAI API key")
        return OpenAIEmbedder(
            model=ref.model, api_key=key, space=space, normalized=normalized, target_dim=target_dim
        )
    raise ValueError(f"Unsupported factory: {factory}")
