import os

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
import ulid

from usecases.persist_document import PersistDocumentCmd, PersistDocumentUseCase

from .dependencies.files import require_markdown_file
from .dtos import IngestMarkdownPayload

router = APIRouter()

DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "default")


def gen_doc_id() -> str:
    return str(ulid.new())


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
    doc_id = pl.doc_id if (pl and pl.doc_id) else gen_doc_id()
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

    if pl.byok is None:
        pl.byok = BYOK()
    if x_voyage_api_key:
        object.__setattr__(pl.byok, "voyage_api_key", x_voyage_api_key)

    chunker = container.make_chunker(method=pl.chunk_method, config=pl.parser_config)
    embed_client = container.make_embedding_client(pl.byok)
    dim = pl.target_dim() or (1024 if getattr(pl, "use_contextualized_chunks", True) else 1024)
    index = container.make_vector_index(dim=dim)
    raptor_builder = container.make_raptor_builder(pl.raptor_params) if pl.build_tree else None
    deduper = container.make_deduper(pl.dedupe) if pl.dedupe else None

    ingest_uc = container.make_ingest_and_index_uc(
        chunker=chunker,
        embed_client=embed_client,
        vector_index=index,
        raptor_builder=raptor_builder,
        deduper=deduper,
        batch_size=pl.batch_size,
    )

    result = await ingest_uc.execute(
        IngestAndIndexCmd(
            dataset_id=dataset_id,
            doc_id=doc_id,
            full_text=file_text,
            embedding_cfg=pl.embedding,
            use_cce=getattr(pl, "use_contextualized_chunks", True),  # BẬT CCE
            build_tree=pl.build_tree,
            upsert_mode=pl.upsert_mode,
        )
    )

    return {
        "code": 200,
        "message": "Embedded",
        "data": {
            "doc_id": doc_id,
            "dataset_id": dataset_id,
            "status": "embedded",
            "chunks": result.chunks,
            "indexed": result.index_stats,
            "raptor_tree_id": result.tree_id,
            "source_uri": res.source_uri,
            "checksum": res.checksum,
        },
    }
