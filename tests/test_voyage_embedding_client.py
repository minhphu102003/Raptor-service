import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
import voyageai

from infra.embeddings.voyage_client import VoyageEmbeddingClientAsync


def make_chunk_fn() -> "Callable[[str], list[str]]":
    size = int(os.getenv("CHUNK_SIZE", "1200"))
    overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=size,
            chunk_overlap=overlap,
            keep_separator=False,
            separators=["\n\n", "\n", " ", ""],
        )
        return lambda doc: splitter.split_text(doc)
    except Exception:

        def split_simple(doc: str, size=size, overlap=overlap):
            out, i, n = [], 0, len(doc)
            while i < n:
                j = min(i + size, n)
                out.append(doc[i:j])
                if j == n:
                    break
                i = max(j - overlap, j) if overlap > 0 else j
            return out

        return split_simple


def _head(x, k=8):
    return x[:k] if isinstance(x, list) else x


async def main():
    load_dotenv()
    api_key = os.getenv("VOYAGEAI_KEY") or os.getenv("VOYAGE_API_KEY")
    assert api_key, "Thiếu VOYAGEAI_KEY/VOYAGE_API_KEY"

    model = os.getenv("VOYAGE_MODEL", "voyage-context-3")
    out_dim = int(os.getenv("OUTPUT_DIM", "1024"))
    out_dtype = os.getenv("OUTPUT_DTYPE", "float")
    use_chunk = True

    path = Path("data/md/ba5f92d452fbff52a0c04067dc59bc4b27486a90c573b07b4e6e5a07ad5b5247.md")
    text = (
        path.read_text(encoding="utf-8", errors="ignore")
        if path.exists()
        else "This is a tiny document for full-text embedding."
    )

    client = VoyageEmbeddingClientAsync(
        api_key=api_key, model=model, out_dim=out_dim, out_dtype=out_dtype
    )

    embs, chunk_texts = await client.embed_doc_fulltext(
        text, chunk=use_chunk, chunk_fn=make_chunk_fn() if use_chunk else None
    )

    out = {
        "num_embeddings": len(embs),
        "embedding_dim": len(embs[0]) if embs else 0,
        "has_chunk_texts": bool(chunk_texts),
        "chunk_texts_sample": (chunk_texts[:2] if chunk_texts else None),
        "first_embedding_head": (_head(embs[0]) if embs else None),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
