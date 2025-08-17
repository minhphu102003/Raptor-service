from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from interfaces_adaptor.ports import (
    Chunk,
    IChunker,
    IDeduper,
    IEmbeddingClient,
    IRaptorBuilder,
    IVectorIndex,
)


@dataclass
class IngestAndIndexCmd:
    dataset_id: str
    doc_id: str
    full_text: str
    embedding_cfg: Any
    use_cce: bool = True
    build_tree: bool = False
    upsert_mode: str = "upsert"


@dataclass
class IngestAndIndexResult:
    chunks: int
    index_stats: Dict[str, Any]
    tree_id: Optional[str] = None


class IngestAndIndexUseCase:
    def __init__(
        self,
        chunker: IChunker,
        embed_client: IEmbeddingClient,
        vector_index: IVectorIndex,
        raptor_builder: Optional[IRaptorBuilder] = None,
        deduper: Optional[IDeduper] = None,
        batch_size: int = 64,
    ):
        self.chunker = chunker
        self.embed_client = embed_client
        self.vector_index = vector_index
        self.raptor_builder = raptor_builder
        self.deduper = deduper
        self.batch_size = batch_size

    async def execute(self, cmd: IngestAndIndexCmd) -> IngestAndIndexResult:
        chunks = self.chunker.chunk(cmd.full_text)
        if self.deduper:
            chunks = self.deduper.filter(chunks)

        texts = [c.text for c in chunks]
        cfg = cmd.embedding_cfg
        model = cfg.embedding_model
        out_dim = getattr(cfg, "output_dimension", None) or cfg.embedding_dim
        out_dtype = getattr(cfg, "output_dtype", None)
        vectors: List[List[float]]

        if cmd.use_cce:
            if not model.startswith("voyage-context"):
                model = "voyage-context-3"
            vectors = await self.embed_client.embed_contextualized(
                texts, model=model, output_dimension=out_dim, output_dtype=out_dtype
            )
        else:
            input_type = getattr(cfg, "input_type", "document") or "document"
            vectors = await self.embed_client.embed_documents(
                texts,
                model=model,
                input_type=input_type,
                output_dimension=out_dim,
                output_dtype=out_dtype,
            )

        items = []
        for c, v in zip(chunks, vectors):
            items.append(
                {
                    "id": f"{cmd.doc_id}:{c.order}",
                    "vector": v,
                    "payload": {
                        "doc_id": cmd.doc_id,
                        "order": c.order,
                        "text": c.text,
                        **c.meta,
                    },
                }
            )

        stats = await self.vector_index.upsert(
            items, namespace=cmd.dataset_id, upsert_mode=cmd.upsert_mode
        )

        tree_id = None
        if cmd.build_tree and self.raptor_builder:
            tree_id = await self.raptor_builder.build(chunks)

        return IngestAndIndexResult(chunks=len(chunks), index_stats=stats, tree_id=tree_id)
