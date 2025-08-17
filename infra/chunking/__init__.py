from typing import List

from interfaces_adaptor.ports import Chunk, IChunker


class NaiveChunker(IChunker):
    def __init__(self, token_limit=512, overlap=100):
        self.token_limit = token_limit
        self.overlap = overlap

    def chunk(self, full_text: str) -> List[Chunk]:
        # TODO: thay bằng tokenizer thực sự; demo cắt theo ký tự
        chunks, order = [], 0
        step = max(1, self.token_limit - self.overlap)
        for i in range(0, len(full_text), step):
            piece = full_text[i : i + self.token_limit]
            if not piece:
                break
            chunks.append(Chunk(id=f"{order}", order=order, text=piece, meta={}))
            order += 1
        return chunks


def make_chunker(method, cfg):
    if method == "naive":
        return NaiveChunker(token_limit=cfg.chunk_token_num, overlap=cfg.overlap_tokens)
    # TODO: markdown/semantic
    raise NotImplementedError(method)
