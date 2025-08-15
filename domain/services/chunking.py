from typing import List

from .tokenizer import rough_token_count


def naive_chunk(
    text: str, tokens_per_chunk: int, overlap: int = 100, delimiter: str = "\n"
) -> List[str]:
    parts = [p.strip() for p in text.split(delimiter)]
    parts = [p for p in parts if p]

    chunks, buf = [], []
    buf_tok = 0

    for p in parts:
        tcount = rough_token_count(p)
        if buf_tok + tcount <= tokens_per_chunk:
            buf.append(p)
            buf_tok += tcount
        else:
            if buf:
                chunks.append(delimiter.join(buf).strip())
            if overlap > 0 and chunks:
                tail = chunks[-1].split(delimiter)
                tail_tokens, keep = 0, []
                for s in reversed(tail):
                    keep.append(s)
                    tail_tokens += rough_token_count(s)
                    if tail_tokens >= overlap:
                        break
                keep.reverse()
                buf = keep[:]
                buf_tok = sum(rough_token_count(s) for s in keep)
            else:
                buf, buf_tok = [], 0
            buf.append(p)
            buf_tok += tcount

    if buf:
        chunks.append(delimiter.join(buf).strip())

    return chunks
