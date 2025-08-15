import uuid

from domain.services.chunking import naive_chunk
from domain.services.normalize import maybe_normalize
from domain.services.validators import ensure_dim, ensure_finite
from interfaces_adaptor.ports import (
    IChatLLM,
    IDocumentRepository,
    IEmbedder,
    IFileSource,
    IQueue,
    IVectorIndex,
)

from .types import IngestResult


def gen_id() -> str:
    return uuid.uuid7().hex if hasattr(uuid, "uuid7") else uuid.uuid4().hex


class IngestMarkdownUseCase:
    def __init__(
        self,
        *,
        file_source: IFileSource,
        embedder: IEmbedder,
        index: IVectorIndex,
        doc_repo: IDocumentRepository,
        queue: IQueue | None = None,
        summarizer: IChatLLM | None = None,
    ):
        self.file_source = file_source
        self.embedder = embedder
        self.index = index
        self.doc_repo = doc_repo
        self.queue = queue
        self.summarizer = summarizer

    async def execute(
        self, file_bytes: bytes | None, file_url: str | None, payload
    ) -> IngestResult:
        # 1) load
        text = await self.file_source.load_markdown(file_bytes, file_url)
        # 2) preprocess + chunk
        cfg = payload.parser_config or type("C", (), {})()
        tokens_per_chunk = getattr(cfg, "chunk_token_num", 512)
        delimiter = getattr(cfg, "delimiter", "\n")
        chunks_txt = naive_chunk(
            text, tokens_per_chunk=tokens_per_chunk, overlap=100, delimiter=delimiter
        )

        # 3) embed
        vectors = await self.embedder.embed(chunks_txt, batch_size=payload.batch_size)
        ensure_finite(vectors)
        if getattr(payload.embedding, "embedding_dim", None):
            ensure_dim(vectors, payload.embedding.embedding_dim)
        vectors = maybe_normalize(
            vectors, space=self.embedder.space, normalized=self.embedder.normalized
        )
        # 4) persist meta + upsert
        doc_id = payload.doc_id or gen_id()
        chunk_ids = [f"{doc_id}:{i}" for i in range(len(chunks_txt))]
        meta = [
            {"dataset_id": payload.dataset_id, "doc_id": doc_id, "idx": i}
            for i in range(len(chunks_txt))
        ]

        self.index.upsert(chunk_ids, vectors, meta)
        self.doc_repo.save_document(
            {
                "dataset_id": payload.dataset_id,
                "doc_id": doc_id,
                "source": payload.source,
                "tags": payload.tags,
                "extra_meta": payload.extra_meta,
            }
        )
        self.doc_repo.save_chunks(
            [{"id": cid, "text": t, **m} for cid, t, m in zip(chunk_ids, chunks_txt, meta)]
        )

        # 5) build RAPTOR?
        if payload.build_tree or (getattr(cfg, "raptor", None) and cfg.raptor.use_raptor):
            if payload.mode == "async" and self.queue:
                job_id = self.queue.enqueue(
                    "build_raptor_tree",
                    {
                        "doc_id": doc_id,
                        "dataset_id": payload.dataset_id,
                        "raptor_params": payload.raptor_params.dict()
                        if payload.raptor_params
                        else {},
                    },
                )
                return IngestResult(doc_id=doc_id, chunks=len(chunks_txt), job_id=job_id)
            else:
                tree_id = await BuildRaptorTreeUseCase(...).execute(
                    doc_id, payload.dataset_id, chunk_ids, chunks_txt, vectors, payload
                )
                return IngestResult(doc_id=doc_id, chunks=len(chunks_txt), tree_id=tree_id)

        return IngestResult(doc_id=doc_id, chunks=len(chunks_txt))
