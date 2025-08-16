from typing import List


class MarkdownSplitter:
    def __init__(
        self, tokenizer, chunk_tokens: int, overlap_tokens: int, max_heading_level: int = 3
    ): ...
    def split(self, text: str) -> List[Chunk]:
        # 1) parse heading (#, ##, ###) → section tree
        # 2) giữ nguyên ngữ nghĩa section; nếu section > chunk_tokens ⇒ re-chunk như naive
        # 3) đảm bảo không cắt bảng/code block; tăng overlap ~20–25% nếu cần
        return chunks
