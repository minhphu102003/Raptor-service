from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class EmbeddingSpec(BaseModel):
    provider: str
    model: str
    embedding_dim: int
    space: str = "cosine"
    normalized: bool = True


class NodeIn(BaseModel):
    chunk_id: str
    text: str
    embedding: Optional[List[float]] = None
    meta: Optional[dict[str, Any]] = None


class BuildParams(BaseModel):
    max_cluster: int = 8
    umap: dict = Field(
        default_factory=lambda: {"n_neighbors": 15, "n_components": 8, "metric": "cosine"}
    )
    clusterer: dict = Field(
        default_factory=lambda: {"type": "gmm", "selection": "bic", "threshold": 0.1}
    )
    summary: dict = Field(
        default_factory=lambda: {"max_tokens": 256, "prompt": "Summarize:\n{cluster_content}"}
    )
    levels_cap: int = 0
    reembed_summary: bool = True
