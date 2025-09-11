import logging
import time
from typing import Callable, List, Optional

from interfaces_adaptor.ports import ChunkFnProvider
from services.document.chunk_refine_service import llm_edge_fix_and_reallocate
from services.providers.fpt_llm.fpt_chat_service import get_edge_decider_llm

logger = logging.getLogger("raptor.chunking.langchain")


class LangChainChunker(ChunkFnProvider):
    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
        keep_separator: bool = False,
        *,
        edge_refine: bool = True,
        edge_limit: int = 5,
        max_chars_per_chunk: int = 8000,
        max_passes: int = 2,
        llm=None,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            chunk_overlap = max(0, chunk_size // 5)

        self.size = chunk_size
        self.overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ".", " ", ""]
        self.keep_separator = keep_separator

        self.edge_refine = edge_refine
        self.edge_limit = edge_limit
        self.max_chars_per_chunk = max_chars_per_chunk
        self.max_passes = max_passes
        self.llm = llm

    def build(self) -> Callable[[str], List[str]]:
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError as e:
            logger.exception("Missing dependency 'langchain-text-splitters'")
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

        def chunk_fn(text: str) -> List[str]:
            logger.info("Chunker: input_len=%d text='%s'", len(text or ""), text)

            chunks = splitter.split_text(text or "")

            chunks = [c for c in chunks if c.strip()]

            # TODO: uncomment this comment below if just using naive chunking

            return chunks

            # 2) Edge refine bằng LLM
            # try:
            #     llm = self.llm or get_edge_decider_llm()
            #     llm_name = getattr(llm, "model_name", getattr(llm, "model", "LLM"))
            #     logger.info(
            #         "Chunker: refine_start llm=%s edge_limit=%d passes=%d",
            #         llm_name,
            #         self.edge_limit,
            #         self.max_passes,
            #     )

            #     refined = llm_edge_fix_and_reallocate(
            #         chunks,
            #         llm=llm,
            #         edge_limit=self.edge_limit,
            #         max_chars_per_chunk=self.max_chars_per_chunk,
            #         max_passes=self.max_passes,
            #     )
            # except Exception:
            #     logger.exception("Chunker: refine_failed — fallback to naive chunks")
            #     refined = chunks

            # refined = [c for c in refined if c.strip()]
            # r_lens = [len(c) for c in refined]

            # logger.info(
            #     "Chunker: refined_len_stats min=%d p50=%d p90=%d max=%d first='%s' last='%s'",
            #     min(r_lens),
            #     sorted(r_lens)[len(r_lens) // 2],
            #     sorted(r_lens)[int(0.9 * len(r_lens))],
            #     max(r_lens),
            #     refined[0],
            #     refined[-1],
            # )
            # return refined

        return chunk_fn
