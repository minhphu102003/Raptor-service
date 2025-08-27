import asyncio
import logging

from repositories import ChunkRepoPg, EmbeddingRepoPg, TreeRepoPg
from services import (
    ChunkService,
    EmbeddingService,
    GMMRaptorClusterer,
    LLMSummarizer,
    PersistDocumentCmd,
    PersistDocumentUseCase,
    RaptorBuildService,
    VoyageEmbedderAdapter,
    make_llm,
)
from services.voyage import VoyageEmbeddingClientAsync
from utils import gen_doc_id, resolve_dataset_id
from utils.lll_sumary import get_llm_from_payload

storage_log = logging.getLogger("storage")


class DocumentService:
    def __init__(self, container):
        self.container = container

    async def purge_dataset(self, dataset_id: str) -> list[str]:
        async with self.container.make_uow() as uow:
            tree_repo = TreeRepoPg(uow.session)
            emb_repo = EmbeddingRepoPg(uow.session)
            deleted_tree_ids = await tree_repo.delete_by_dataset(dataset_id)
            if deleted_tree_ids:
                await emb_repo.delete_by_tree_ids(deleted_tree_ids)
            return deleted_tree_ids

    async def list_chunks_now(self, dataset_id: str):
        async with self.container.make_uow() as uow:
            chunk_repo = ChunkRepoPg(uow.session)
            return await chunk_repo.list_by_dataset_join(dataset_id=dataset_id)

    async def list_embeddings_now(self, dataset_id: str):
        async with self.container.make_uow() as uow:
            emb_repo = EmbeddingRepoPg(uow.session)
            return await emb_repo.list_owner_vectors_by_dataset(dataset_id=dataset_id)

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
        vectors, chunk_texts = await cce.embed_doc_fulltext_multi(
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
            raise
        chunk_items_1 = []
        vectors_1 = []
        async with self.container.make_uow() as check_uow:
            doc_repo = self.container.make_doc_repo(check_uow)
            exists = await doc_repo.dataset_has_more_than_one(dataset_id)
            if exists:
                if hasattr(asyncio, "TaskGroup"):
                    async with asyncio.TaskGroup() as tg:
                        t_purge = tg.create_task(self.purge_dataset(dataset_id))
                        t_chunks = tg.create_task(self.list_chunks_now(dataset_id))
                    _deleted_tree_ids = t_purge.result()
                    list_chunk = t_chunks.result()
                else:
                    _deleted_tree_ids, list_chunk = await asyncio.gather(
                        self.purge_dataset(dataset_id),
                        self.list_chunks_now(dataset_id),
                    )
                list_emb = await self.list_embeddings_now(dataset_id)
                emb_map = {owner_id: vec for owner_id, vec in list_emb}
                for i, (cid, txt) in enumerate(list_chunk):
                    v = emb_map.get(cid)
                    if v is None:
                        continue
                    chunk_items_1.append({"id": cid, "text": txt, "idx": i})
                    vectors_1.append(v)

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
            base_items = [
                {"id": cid, "text": txt, "idx": i}
                for i, (cid, txt) in enumerate(zip(chunk_ids, chunk_texts))
            ]
            base_vecs = list(vectors)

            if len(chunk_items_1) > 0 and len(vectors_1) > 0:
                assert len(chunk_items_1) == len(vectors_1), (
                    f"length mismatch: items={len(chunk_items_1)} vs vecs={len(vectors_1)}"
                )
                items, vecs = chunk_items_1, vectors_1

                storage_log.info(
                    "[RAPTOR] build: USING EXTRA chunks (historical) — new=%d extra=%d",
                    len(base_items),
                    len(chunk_items_1),
                )
                if storage_log.isEnabledFor(logging.DEBUG):
                    extra_ids = [it["id"] for it in chunk_items_1[:10]]
                    storage_log.debug("[RAPTOR] extra_ids(sample<=10)=%s", extra_ids)
            else:
                items, vecs = base_items, base_vecs
                storage_log.info(
                    "[RAPTOR] build: USING ONLY NEW chunks — new=%d (no extra)", len(base_items)
                )
                if storage_log.isEnabledFor(logging.DEBUG):
                    new_ids = [it["id"] for it in base_items[:10]]
                    storage_log.debug("[RAPTOR] new_ids(sample<=10)=%s", new_ids)

            tree_id = await raptor.build_from_memory_pairs(
                doc_id=doc_id,
                dataset_id=dataset_id,
                chunk_items=items,
                vectors=vecs,
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
