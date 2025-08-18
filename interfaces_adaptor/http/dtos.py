import os
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator


class RaptorConfig(BaseModel):
    use_raptor: bool = True


class ParserConfigGeneric(BaseModel):
    model_config = ConfigDict(extra="allow")
    raptor: Optional[RaptorConfig] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class SummaryLLM(BaseModel):
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 1024
    use_builtin: bool = True


class BYOK(BaseModel):
    openai_api_key: Optional[str] = None
    azure_openai: Optional[Dict[str, str]] = None
    cohere_api_key: Optional[str] = None
    huggingface_token: Optional[str] = None
    dashscope_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    voyage_api_key: Optional[str] = None


class RaptorParams(BaseModel):
    levels_cap: Optional[int] = None
    summary_max_tokens: Optional[int] = None
    reembed_summary: bool = False
    clusterer: Optional[Dict[str, Any]] = None
    umap: Optional[Dict[str, Any]] = None


class IngestMarkdownPayload(BaseModel):
    dataset_id: str
    doc_id: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    extra_meta: Optional[Dict[str, Any]] = None
    build_tree: bool = True
    raptor_params: Optional[RaptorParams] = None
    summary_llm: Optional[SummaryLLM] = None
    auto_embed: bool = True
    batch_size: int = 64
    vector_index: Optional[Dict[str, Any]] = None
    upsert_mode: Literal["upsert", "replace", "skip_duplicates"] = "upsert"
    dedupe: Optional[Dict[str, Any]] = None
    mode: Literal["sync", "async"] = "sync"
    byok: Optional[BYOK] = None
