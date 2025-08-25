import logging

from infra.embeddings import VoyageEmbeddingClientAsync
from interfaces_adaptor.repositories import ChunkRepoPg, EmbeddingRepoPg, TreeRepoPg
from services import (
    GEMINI_FAST,
    ChunkService,
    EmbeddingService,
    GMMRaptorClusterer,
    LLMSummarizer,
    RaptorBuildService,
    VoyageEmbedderAdapter,
    make_llm,
)
from usecases import PersistDocumentCmd, PersistDocumentUseCase
from utils import gen_doc_id, resolve_dataset_id
from utils.lll_sumary import get_llm_from_payload

storage_log = logging.getLogger("storage")


class DocumentService:
    def __init__(self, container):
        self.container = container

    async def ingest_markdown(self, file_bytes: bytes, pl, x_dataset_id: str | None):
        file_text = file_bytes.decode("utf-8", errors="ignore")
        doc_id = gen_doc_id()
        dataset_id = resolve_dataset_id(pl, x_dataset_id)

        async with self.container.make_uow() as uow:
            doc_repo = self.container.make_doc_repo(uow)
            uc = PersistDocumentUseCase(
                file_source=self.container.file_source, doc_repo=doc_repo, uow=uow
            )
            cmd = PersistDocumentCmd(
                dataset_id=dataset_id,
                doc_id=doc_id,
                file_bytes=file_bytes,
                source=(pl.source if pl else None),
                tags=(pl.tags if pl else None),
                extra_meta=(pl.extra_meta if pl else None),
                upsert_mode=(pl.upsert_mode if pl else "upsert"),
                text=file_text,
            )
            res = await uc.execute(cmd)

        cce = VoyageEmbeddingClientAsync(model="voyage-context-3")
        vectors, chunk_texts = await cce.embed_doc_fulltext_rate_limited(
            text=file_text,
            chunk_fn=self.container.chunk_fn,
        )

        async with self.container.make_uow() as chunk_uow:
            chunk_service = ChunkService(chunk_uow.session)
            chunk_ids = await chunk_service.store_chunks(
                doc_id=doc_id,
                dataset_id=dataset_id,
                chunk_texts=chunk_texts,
                source_uri=res.source_uri,
                extra_meta=pl.extra_meta or {},
                start_index=0,
            )
            await chunk_uow.commit()

        try:
            async with self.container.make_uow() as emb_uow:
                storage_log.info(
                    "[STORAGE] upsert start dataset=%s doc=%s rows=%d dim=%d model=%s",
                    dataset_id,
                    doc_id,
                    len(chunk_ids),
                    1024,
                    "voyage-3",
                )

                emb_service = EmbeddingService(emb_uow.session)
                await emb_service.store_embeddings(
                    dataset_id=dataset_id,
                    owner_type="chunk",
                    owner_ids=chunk_ids,
                    vectors=vectors,
                    model="voyage-context-3",
                    dim=1024,
                    extra_meta={"doc_id": doc_id},
                )
                await emb_uow.commit()
        except Exception:
            storage_log.exception("[STORAGE] upsert FAILED dataset=%s doc=%s", dataset_id, doc_id)

        # TODO : checking in here whether we need rebuild raptor or not

        async with self.container.make_uow() as raptor_uow:
            tree_repo = TreeRepoPg(raptor_uow.session)
            emb_repo = EmbeddingRepoPg(raptor_uow.session)
            chunk_repo = ChunkRepoPg(raptor_uow.session)

            embedder = VoyageEmbedderAdapter(cce)
            clusterer = GMMRaptorClusterer()
            llm = get_llm_from_payload(pl)
            summarizer = LLMSummarizer(llm)

            raptor = RaptorBuildService(
                embedder=embedder,
                clusterer=clusterer,
                summarizer=summarizer,
                tree_repo=tree_repo,
                emb_repo=emb_repo,
                chunk_repo=chunk_repo,
            )
            tree_id = await raptor.build_from_memory_pairs(
                doc_id=doc_id,
                dataset_id=dataset_id,
                chunk_items=[
                    {"id": cid, "text": txt, "idx": i}
                    for i, (cid, txt) in enumerate(zip(chunk_ids, chunk_texts))
                ],
                vectors=vectors,
                params={"min_k": 2, "max_k": 50, "max_tokens": 512},
            )

        return {
            "code": 200,
            "data": {
                "doc_id": doc_id,
                "dataset_id": dataset_id,
                "status": "embedded",
                "chunks": len(chunk_ids),
                "indexed": {"upserted": len(chunk_ids)},
                "tree_id": tree_id,
                "checksum": res.checksum,
            },
        }
