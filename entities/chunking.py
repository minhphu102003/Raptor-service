from typing import Dict, Literal, Optional, Protocol

from pydantic import BaseModel

ChunkMethod = Literal["naive", "markdown", "semantic"]


class Chunk(BaseModel):
    chunk_id: str
    text: str
    meta: Dict[str, object] = {}


class DocumentKind(str):
    pass


class ChunkingDecision(BaseModel):
    method: ChunkMethod
    chunk_token_num: int
    overlap_tokens: int
    delimiter: str = "\n"
    enable_raptor: bool = False
    raptor_levels_cap: Optional[int] = 0
    summary_max_tokens: Optional[int] = 200
    reembed_summary: bool = True


class ChunkingPolicy(Protocol):
    def decide(
        self, *, doc_kind: str, goal: str, text_stats: Dict[str, int]
    ) -> ChunkingDecision: ...
