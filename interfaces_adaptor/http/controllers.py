from fastapi import APIRouter, File, Form, Header, UploadFile
from pydantic import ValidationError

from app.container import container
from interfaces_adaptor.http.factories import make_embedder
from usecases.ingest_markdown import IngestMarkdownUseCase

from .dtos import IngestMarkdownPayload

router = APIRouter()


@router.post("/v1/documents:ingest-markdown")
async def ingest_markdown(
    file: UploadFile | None = File(default=None),
    payload: str = Form(...),
    x_openai_api_key: str | None = Header(default=None, alias="X-OpenAI-Api-Key"),
    x_azure_openai_api_key: str | None = Header(default=None, alias="X-Azure-OpenAI-Api-Key"),
    x_azure_openai_endpoint: str | None = Header(default=None, alias="X-Azure-OpenAI-Endpoint"),
    x_azure_openai_deployment: str | None = Header(default=None, alias="X-Azure-OpenAI-Deployment"),
    x_cohere_api_key: str | None = Header(default=None, alias="X-Cohere-Api-Key"),
    x_hf_token: str | None = Header(default=None, alias="X-HF-Token"),
    x_dashscope_api_key: str | None = Header(default=None, alias="X-Dashscope-Api-Key"),
    x_gemini_api_key: str | None = Header(default=None, alias="X-Gemini-Api-Key"),
):
    try:
        pl = IngestMarkdownPayload.model_validate_json(payload)
    except ValidationError as e:
        return {"code": 400, "message": f"Bad Request: {e.errors()}"}

    hdr_byok = {
        "openai_api_key": x_openai_api_key,
        "azure_openai": (
            {
                "endpoint": x_azure_openai_endpoint,
                "api_key": x_azure_openai_api_key,
                "deployment": x_azure_openai_deployment,
            }
            if x_azure_openai_api_key or x_azure_openai_endpoint
            else None
        ),
        "cohere_api_key": x_cohere_api_key,
        "huggingface_token": x_hf_token,
        "dashscope_api_key": x_dashscope_api_key,
        "gemini_api_key": x_gemini_api_key,
    }
    hdr_byok = {k: v for k, v in hdr_byok.items() if v}

    byok = hdr_byok or (pl.byok.model_dump() if pl.byok else None)

    embedder = make_embedder(
        embedding_model=pl.embedding.embedding_model,
        space=pl.embedding.space,
        normalized=pl.embedding.normalized,
        byok=byok,
        target_dim=pl.embedding.embedding_dim,
    )

    dim = pl.embedding.embedding_dim or getattr(embedder, "dim", None)
    if not dim:
        return {"code": 400, "message": "Cannot determine embedding_dim"}
    index = container.make_vector_index(dim=dim)

    usecase = IngestMarkdownUseCase(
        file_source=container.file_source,
        embedder=embedder,
        index=index,
        doc_repo=container.doc_repo,
        queue=None,
        summarizer=None,
    )

    if pl.mode == "async" and (
        pl.build_tree
        or (getattr(pl.parser_config, "raptor", None) and pl.parser_config.raptor.use_raptor)
    ):
        job_id = "job_..."  # TODO: container.queue.enqueue(...)
        return {"code": 0, "message": "Accepted", "data": {"job_id": job_id}}, 202

    file_bytes = await file.read() if file is not None else None
    result = await usecase.execute(
        file_bytes=file_bytes, file_url=str(pl.file_url) if pl.file_url else None, payload=pl
    )

    return {"code": 0, "message": "", "data": result.__dict__}
