import os
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

ChunkMethod = Literal["naive", "markdown", "semantic"]


class RaptorConfig(BaseModel):
    use_raptor: bool = True


class ParserConfigNaive(BaseModel):
    chunk_token_num: int = 512
    overlap_tokens: int = Field(default=100, ge=0, le=2000)
    delimiter: str = "\n"
    html4excel: bool = False
    layout_recognize: bool = True
    raptor: RaptorConfig = RaptorConfig()


class ParserConfigGeneric(BaseModel):
    model_config = ConfigDict(extra="allow")
    raptor: Optional[RaptorConfig] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class RagflowStyleEmbedding(BaseModel):
    embedding_model: str
    embedding_dim: Optional[int] = None
    space: Literal["cosine", "ip", "l2"] = "cosine"
    normalized: bool = True

    @model_validator(mode="after")
    def _cosine_requires_norm(self):
        if self.space == "cosine" and not self.normalized:
            object.__setattr__(self, "normalized", True)
        return self


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

    @model_validator(mode="after")
    def _fill_voyage_from_env(self):
        if self.voyage_api_key is None:
            env = os.getenv("VOYAGE_API_KEY")
            if env:
                object.__setattr__(self, "voyage_api_key", env)
        return self


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
    chunk_method: ChunkMethod = "naive"
    parser_config: Optional[ParserConfigNaive | ParserConfigGeneric] = None
    embedding: RagflowStyleEmbedding
    build_tree: bool = False
    raptor_params: Optional[RaptorParams] = None
    summary_llm: Optional[SummaryLLM] = None
    auto_embed: bool = True
    batch_size: int = 64
    vector_index: Optional[Dict[str, Any]] = None
    upsert_mode: Literal["upsert", "replace", "skip_duplicates"] = "upsert"
    dedupe: Optional[Dict[str, Any]] = None
    mode: Literal["sync", "async"] = "sync"
    byok: Optional[BYOK] = None

    @model_validator(mode="after")
    def _default_parser_config(self):
        # nếu chunk_method=naive mà chưa có config → tạo mặc định
        if self.chunk_method == "naive" and (
            self.parser_config is None or isinstance(self.parser_config, ParserConfigGeneric)
        ):
            self.parser_config = ParserConfigNaive()
        return self

    @model_validator(mode="after")
    def _sync_build_tree_with_parser(self):
        # nếu parser_config.raptor.use_raptor == True → bật build_tree
        r = getattr(self.parser_config, "raptor", None)
        if r and getattr(r, "use_raptor", False):
            object.__setattr__(self, "build_tree", True)
        return self

    def target_dim(self) -> Optional[int]:
        # giá trị bạn sẽ truyền xuống embedder để ép số chiều (dimensions)
        return self.embedding.embedding_dim
