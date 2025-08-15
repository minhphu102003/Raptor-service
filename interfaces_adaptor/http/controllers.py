import os

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from pydantic import ValidationError
import ulid

from interfaces_adaptor.http.factories import make_embedder
from usecases.ingest_markdown import IngestMarkdownUseCase
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
):
    container = request.app.state.container

    pl = None
    if payload:
        try:
            pl = IngestMarkdownPayload.model_validate_json(payload)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.errors())

    file_bytes = await file.read() if file is not None else None
    file_url = str(pl.file_url) if (pl and pl.file_url) else None

    if not file_bytes and not file_url:
        return {"code": 400, "message": "file (multipart) hoặc file_url (payload) là bắt buộc"}

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
        file_url=(str(pl.file_url) if pl and pl.file_url else None),
        source=(pl.source if pl and pl.source else None),
        tags=(pl.tags if pl else None),
        extra_meta=(pl.extra_meta if pl else None),
        upsert_mode=(pl.upsert_mode if pl else "upsert"),
    )

    res = await uc.execute(cmd)

    if not pl or (pl and not pl.auto_embed):
        return {
            "code": 0,
            "message": "Persisted",
            "data": {
                "doc_id": res.doc_id,
                "dataset_id": res.dataset_id,
                "status": "stored",
                "source_uri": res.source_uri,
                "checksum": res.checksum,
            },
        }

    # hdr_byok = {
    #     "openai_api_key": x_openai_api_key,
    #     "azure_openai": (
    #         {
    #             "endpoint": x_azure_openai_endpoint,
    #             "api_key": x_azure_openai_api_key,
    #             "deployment": x_azure_openai_deployment,
    #         }
    #         if x_azure_openai_api_key or x_azure_openai_endpoint
    #         else None
    #     ),
    #     "cohere_api_key": x_cohere_api_key,
    #     "huggingface_token": x_hf_token,
    #     "dashscope_api_key": x_dashscope_api_key,
    #     "gemini_api_key": x_gemini_api_key,
    # }
    # hdr_byok = {k: v for k, v in hdr_byok.items() if v}

    # byok = hdr_byok or (pl.byok.model_dump() if pl.byok else None)

    # embedder = make_embedder(
    #     embedding_model=pl.embedding.embedding_model,
    #     space=pl.embedding.space,
    #     normalized=pl.embedding.normalized,
    #     byok=byok,
    #     target_dim=pl.embedding.embedding_dim,
    # )

    # dim = pl.embedding.embedding_dim or getattr(embedder, "dim", None)
    # if not dim:
    #     return {"code": 400, "message": "Cannot determine embedding_dim"}
    # index = container.make_vector_index(dim=dim)

    # usecase = IngestMarkdownUseCase(
    #     file_source=container.file_source,
    #     embedder=embedder,
    #     index=index,
    #     doc_repo=container.doc_repo,
    #     queue=None,
    #     summarizer=None,
    # )

    # if pl.mode == "async" and (
    #     pl.build_tree
    #     or (getattr(pl.parser_config, "raptor", None) and pl.parser_config.raptor.use_raptor)
    # ):
    #     job_id = "job_..."
    #     # TODO: container.queue.enqueue(...)
    #     return {"code": 0, "message": "Accepted", "data": {"job_id": job_id}}, 202

    # file_bytes = await file.read() if file is not None else None
    # result = await usecase.execute(
    #     file_bytes=file_bytes, file_url=str(pl.file_url) if pl.file_url else None, payload=pl
    # )

    # return {"code": 0, "message": "", "data": result.__dict__}
    return {"code": 0, "message": "", "data": res}
