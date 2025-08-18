from typing import Callable, List, Optional, Tuple

import voyageai


def to_voyage_chunk_fn(chunker):
    if hasattr(chunker, "split_text"):
        return lambda doc: chunker.split_text(doc)
    if hasattr(chunker, "split"):
        return lambda doc: chunker.split(doc)
    return voyageai.default_chunk_fn


class VoyageEmbeddingClientAsync:
    def __init__(
        self,
        api_key: str,
        model: str = "voyage-context-3",
        out_dim: int = 1024,
        out_dtype: str = "float",
    ):
        self.vo = voyageai.AsyncClient(api_key=api_key)
        self.model = model
        self.out_dim = out_dim
        self.out_dtype = out_dtype

    async def embed_doc_fulltext(
        self,
        text: str,
        *,
        chunk_fn: Optional[Callable[[str], list[str]]] = None,
    ) -> Tuple[List[List[float]], Optional[List[str]]]:
        kwargs = {"chunk_fn": chunk_fn} if chunk_fn else {}

        r = await self.vo.contextualized_embed(
            inputs=[[text]],
            model=self.model,
            input_type="document",
            output_dimension=self.out_dim,
            output_dtype=self.out_dtype,
            **kwargs,
        )
        res = r.results[0]
        return res.embeddings, getattr(res, "chunk_texts", None)

    async def embed_queries(self, queries: List[str]) -> List[List[float]]:
        r = await self.vo.contextualized_embed(
            inputs=[[q] for q in queries],
            model=self.model,
            input_type="query",
            output_dimension=self.out_dim,
            output_dtype=self.out_dtype,
        )
        return [res.embeddings[0] for res in r.results]
