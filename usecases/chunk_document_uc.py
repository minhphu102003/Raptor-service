from typing import Dict

from entities.chunking import ChunkingDecision, ChunkingPolicy


class DefaultChunkingPolicy:
    def __init__(self, tokenizer: "Tokenizer"):
        self.tok = tokenizer

    def decide(self, *, doc_kind: str, goal: str, text_stats: Dict[str, int]) -> ChunkingDecision:
        if goal == "qa":
            size = 256
            overlap = 40
        else:
            size = 400
            overlap = 60

        if doc_kind == "markdown":
            return ChunkingDecision(method="markdown", chunk_token_num=size, overlap_tokens=overlap)
        return ChunkingDecision(method="naive", chunk_token_num=size, overlap_tokens=overlap)
