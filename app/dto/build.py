from __future__ import annotations

from typing import List

from pydantic import BaseModel

from .common import BuildParams, EmbeddingSpec, NodeIn


class BuildRequest(BaseModel):
    dataset_id: str
    tree_id: str | None = None
    embedding_spec: EmbeddingSpec
    nodes: List[NodeIn]
    params: BuildParams
    mode: str = "sync"


class BuildResponse(BaseModel):
    tree_id: str
    dataset_id: str
    stats: dict
    root_node_id: str
    vector_index: dict
