from typing import List


class NaiveSplitter:
    def __init__(
        self, tokenizer, chunk_tokens: int, overlap_tokens: int, delimiter: str = "\n"
    ): ...

    def split(self, text: str) -> List[Chunk]:
        return chunks
