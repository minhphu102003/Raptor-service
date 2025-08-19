import asyncio
import os
import uuid

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
from services.chunk_service import ChunkService
from services.embedding_service import EmbeddingService
from usecases.persist_document import PersistDocumentCmd, PersistDocumentUseCase

from .dependencies.files import require_markdown_file
from .dtos import IngestMarkdownPayload

router = APIRouter()

DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "default")


def gen_doc_id() -> str:
    return uuid.uuid4().hex


def resolve_dataset_id(pl: IngestMarkdownPayload | None, x_dataset_id: str | None) -> str:
    return (pl.dataset_id if pl and pl.dataset_id else x_dataset_id) or DEFAULT_DATASET_ID


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
    x_openai_api_key: str | None = Header(default=None, alias="X-OpenAI-Api-Key"),
    x_azure_openai_api_key: str | None = Header(default=None, alias="X-Azure-OpenAI-Api-Key"),
    x_azure_openai_endpoint: str | None = Header(default=None, alias="X-Azure-OpenAI-Endpoint"),
    x_azure_openai_deployment: str | None = Header(default=None, alias="X-Azure-OpenAI-Deployment"),
    x_cohere_api_key: str | None = Header(default=None, alias="X-Cohere-Api-Key"),
    x_hf_token: str | None = Header(default=None, alias="X-HF-Token"),
    x_dashscope_api_key: str | None = Header(default=None, alias="X-Dashscope-Api-Key"),
    x_gemini_api_key: str | None = Header(default=None, alias="X-Gemini-Api-Key"),
    x_voyage_api_key: str | None = Header(default=None, alias="X-Voyage-Api-Key"),
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
    if not pl or (pl and not pl.auto_embed):
        return {
            "code": 200,
            "message": "Persisted",
            "data": {
                "doc_id": res.doc_id,
                "dataset_id": res.dataset_id,
                "status": "stored",
                "source_uri": res.source_uri,
                "checksum": res.checksum,
            },
        }

    if not getattr(pl.byok, "voyage_api_key", None):
        raise HTTPException(
            status_code=400, detail="Thiếu X-Voyage-Api-Key khi dùng contextualized_embed."
        )

    print("api key ", pl.byok.voyage_api_key)

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
    print("DEBUG ***** 1 : ")

    vectors, chunk_texts = await cce.embed_doc_fulltext_rate_limited(
        text=file_text,
        chunk_fn=container.chunk_fn,
    )

    print("DEBUG ***** 5 : ")
    points = []
    for i, (vec, txt) in enumerate(zip(vectors, chunk_texts)):
        points.append(
            {
                "id": f"{doc_id}::c{i}",
                "vector": vec,
                "metadata": {
                    "doc_id": doc_id,
                    "dataset_id": dataset_id,
                    "chunk_index": i,
                    "text": txt,
                    "source_uri": res.source_uri,
                    **(pl.extra_meta or {}),
                },
            }
        )
    print("DEBUG ***** 6 : ")

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
        async with container.make_uow() as emb_uow:
            emb_service = EmbeddingService(emb_uow.session, n_dim=1024)
            await emb_service.store_embeddings(
                dataset_id=dataset_id,
                owner_type="chunk",
                owner_ids=chunk_ids,
                vectors=vectors,
                model="voyage-3",
                dim=1024,
                extra_meta={"doc_id": doc_id},
            )
            await emb_uow.commit()
        embedded_ok = True
    except Exception as ex:
        print(ex)
        # TODO: write log, trace in here ...
        embedded_ok = False
    print("DEBUG ***** 7 : ")
    return {
        "code": 200,
        "message": "Embedded (CCE)",
        "data": {
            "doc_id": doc_id,
            "dataset_id": dataset_id,
            "status": "embedded",
            "chunks": len(points),
            "indexed": {"upserted": len(points)},
            "raptor_tree_id": None,
            "source_uri": res.source_uri,
            "checksum": res.checksum,
        },
    }
