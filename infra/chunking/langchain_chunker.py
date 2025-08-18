from typing import Callable, List, Optional

from interfaces_adaptor.ports import ChunkFnProvider


class LangChainChunker(ChunkFnProvider):
    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
        keep_separator: bool = False,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            chunk_overlap = max(0, chunk_size // 5)

        self.size = chunk_size
        self.overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]
        self.keep_separator = keep_separator

    def build(self) -> Callable[[str], List[str]]:
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError as e:
            raise RuntimeError(
                "Missing dependency 'langchain-text-splitters'. "
                "Install: pip install langchain-text-splitters"
            ) from e

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.size,
            chunk_overlap=self.overlap,
            keep_separator=self.keep_separator,
            separators=self.separators,
        )
        return splitter.split_text
