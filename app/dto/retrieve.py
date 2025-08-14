from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class RetrieveRequest(BaseModel):
    tree_id: str
    mode: str = "collapsed"
    query: str
    query_embedding: Optional[List[float]] = None
    top_k: int = 8
    with_paths: bool = True
    reranker: Optional[dict] = None
