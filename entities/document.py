from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Chunk:
    id: str
    doc_id: str
    idx: int
    text: str
    token_cnt: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None


@dataclass
class Document:
    doc_id: str
    dataset_id: str
    source: Optional[str] = None
    tags: Optional[list[str]] = None
    extra_meta: Optional[Dict[str, Any]] = None
    chunks: Optional[List[Chunk]] = None
