import logging
import time

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from pydantic import ValidationError

from infra.embeddings.voyage_client import VoyageEmbeddingClientAsync
from interfaces_adaptor.repositories.chunk_repo_pg import ChunkRepoPg
from interfaces_adaptor.repositories.embedding_repo_pg import EmbeddingRepoPg
from interfaces_adaptor.repositories.tree_repo_pg import TreeRepoPg
from services.build_tree_service import RaptorBuildService
from services.chunk_service import ChunkService
from services.clusterer import GMMRaptorClusterer
from services.embedder_adapter import VoyageEmbedderAdapter
from services.embedding_service import EmbeddingService
from services.summarizer import GEMINI_FAST, LLMSummarizer, make_llm
from usecases.persist_document import PersistDocumentCmd, PersistDocumentUseCase
from utils.render_id import gen_doc_id, resolve_dataset_id

from .dependencies.files import require_markdown_file
from .dtos import IngestMarkdownPayload

storage_log = logging.getLogger("storage")

router = APIRouter()


@router.post(
    "/v1/documents:ingest-markdown",
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {"encoding": {"file": {"contentType": "text/markdown"}}}
            }
        }
    },
)
async def ingest_markdown(
    request: Request,
    file: UploadFile = Depends(require_markdown_file),
    payload: str = Form(...),
    x_dataset_id: str | None = Header(default=None, alias="X-Dataset-Id"),
):
    container = request.app.state.container

    pl = None
    if payload:
        try:
            pl = IngestMarkdownPayload.model_validate_json(payload)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.errors())

    file_bytes = await file.read() if file is not None else None

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File upload là bắt buộc"
        )

    file_text = file_bytes.decode("utf-8", errors="ignore")
    doc_id = gen_doc_id()
    dataset_id = resolve_dataset_id(pl, x_dataset_id)

    uow = container.make_uow()
    doc_repo = container.make_doc_repo(uow)
    file_source = container.file_source
    uc = PersistDocumentUseCase(file_source=file_source, doc_repo=doc_repo, uow=uow)

    # TODO: fix issue (relative session issue) in later when we need to rebuild raptor tree
    # is_incremental = await doc_repo.dataset_exists(dataset_id)

    cmd = PersistDocumentCmd(
        dataset_id=dataset_id,
        doc_id=doc_id,
        file_bytes=file_bytes,
        source=(pl.source if pl and pl.source else None),
        tags=(pl.tags if pl else None),
        extra_meta=(pl.extra_meta if pl else None),
        upsert_mode=(pl.upsert_mode if pl else "upsert"),
        text=file_text,
    )
    res = await uc.execute(cmd)

    if not getattr(pl.byok, "voyage_api_key", None):
        raise HTTPException(
            status_code=400, detail="Thiếu X-Voyage-Api-Key khi dùng contextualized_embed."
        )

    cce = VoyageEmbeddingClientAsync(
        api_key=pl.byok.voyage_api_key,
        model="voyage-context-3",
        out_dim=1024,
        out_dtype="float",
        rpm_limit=3,
        tpm_limit=10_000,
        max_retries=3,
        per_request_token_budget=9_500,
    )

    vectors, chunk_texts = await cce.embed_doc_fulltext_rate_limited(
        text=file_text,
        chunk_fn=container.chunk_fn,
    )

    async with container.make_uow() as chunk_uow:
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
        t0 = time.perf_counter()
        async with container.make_uow() as emb_uow:
            emb_service = EmbeddingService(emb_uow.session, n_dim=1024)

            storage_log.info(
                "[STORAGE] upsert start dataset=%s doc=%s rows=%d dim=%d model=%s",
                dataset_id,
                doc_id,
                len(chunk_ids),
                1024,
                "voyage-3",
            )

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
            storage_log.info(
                "[STORAGE] upsert ok dataset=%s doc=%s rows=%d ms=%.1f",
                dataset_id,
                doc_id,
                len(chunk_ids),
                (time.perf_counter() - t0) * 1e3,
            )

    except Exception:
        storage_log.exception(
            "[STORAGE] upsert FAILED dataset=%s doc=%s rows=%d", dataset_id, doc_id, len(chunk_ids)
        )

    is_incremental = False

    chunk_items = [
        {"id": cid, "text": txt, "idx": i}
        for i, (cid, txt) in enumerate(zip(chunk_ids, chunk_texts))
    ]

    if is_incremental:
        # TODO: implement incremental Raptor in future
        pass
    else:
        async with container.make_uow() as raptor_uow:
            tree_repo = TreeRepoPg(raptor_uow.session)
            emb_repo = EmbeddingRepoPg(raptor_uow.session)
            chunk_repo = ChunkRepoPg(raptor_uow.session)

            embedder = VoyageEmbedderAdapter(cce)
            clusterer = GMMRaptorClusterer()
            llm = make_llm(GEMINI_FAST)
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
                chunk_items=chunk_items,
                vectors=vectors,
                params={"min_k": 2, "max_k": 50, "max_tokens": 512},
            )
            logging.info("Built RAPTOR tree_id=%s", tree_id)

    return {
        "code": 200,
        "data": {
            "doc_id": doc_id,
            "dataset_id": dataset_id,
            "status": "embedded",
            "chunks": len(chunk_ids),
            "indexed": {"upserted": len(chunk_ids)},
            "raptor_tree_id": None,
            "source_uri": res.source_uri,
            "checksum": res.checksum,
            "tree_id": tree_id,
        },
    }
