import json
from typing import Annotated, List, Literal, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel

from constants.enum import SummarizeModel
from controllers.dataset_controller import DatasetController
from controllers.document_controller import DocumentController
from interfaces_adaptor.http.dependencies.files import require_markdown_file
from repositories.retrieval_repo import RetrievalRepo
from services.embedding.embedding_query_service import EmbeddingService
from services.providers.fpt_llm.client import FPTLLMClient
from services.providers.gemini_chat.llm import GeminiChatLLM
from services.providers.model_registry import ModelRegistry
from services.providers.openai_chat.openai_client_async import OpenAIClientAsync
from services.providers.voyage.voyage_client import VoyageEmbeddingClientAsync
from services.retrieval.answer_service import AnswerService
from services.retrieval.query_rewrite_service import QueryRewriteService
from services.retrieval.retrieval_service import RetrievalService, RetrieveBody
from utils.json import parse_json_opt

router = APIRouter()

_FPT = FPTLLMClient(model="DeepSeek-V3")
_VOY = VoyageEmbeddingClientAsync(model="voyage-context-3", out_dim=1024)

_REWRITE = QueryRewriteService(fpt_client=_FPT)
_EMBED = EmbeddingService(voyage_client_async=_VOY)
_SERVICE = RetrievalService(rewrite_svc=_REWRITE, embed_svc=_EMBED)
_GEMINI = GeminiChatLLM(model="gemini-2.5-flash")
_OPENAI = OpenAIClientAsync(model="gpt-4o-mini")

_model_registry = ModelRegistry(
    fpt_client=_FPT,
    openai_client=_OPENAI,
    gemini_client=_GEMINI,
    anthropic_client=None,
)

_ANSWER = AnswerService(retrieval_svc=_SERVICE, model_registry=_model_registry)


@router.get("/datasets/{dataset_id}/documents")
async def list_documents_by_dataset(
    dataset_id: str,
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """
    List documents in a specific dataset with pagination.
    This endpoint provides the same functionality as the dataset endpoint
    but follows the documents route pattern.
    """
    controller = DatasetController(request)
    return await controller.get_dataset_documents(dataset_id, page, page_size)


@router.post("/validate-dataset")
async def validate_dataset_for_upload(request: Request, dataset_id: Annotated[str, Form(...)]):
    """
    Validate if a dataset ID is valid and ready for document upload.
    This can be called before uploading to ensure the dataset ID is acceptable.
    """
    controller = DatasetController(request)
    return await controller.validate_dataset(dataset_id)


@router.post("/ingest-markdown")
async def ingest_markdown(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    dataset_id: Annotated[str, Form(...)],
    source: Annotated[Optional[str], Form()] = None,
    tags: Annotated[Optional[List[str]], Form()] = None,
    extra_meta: Annotated[Optional[str], Form()] = None,
    build_tree: Annotated[Optional[bool], Form()] = True,
    summary_llm: Annotated[Optional[SummarizeModel], Form()] = None,
    vector_index: Annotated[Optional[str], Form()] = None,
    upsert_mode: Annotated[Literal["upsert", "replace", "skip_duplicates"], Form()] = "upsert",
    x_dataset_id: Annotated[Optional[str], Header(alias="X-Dataset-Id")] = None,
):
    """
    Ingest a Markdown document into a specified dataset/knowledge base.

    Args:
        file: The Markdown file to upload (.md extension required)
        dataset_id: The target dataset/knowledge base ID
        source: Optional source description
        tags: Optional list of tags for categorization
        extra_meta: Optional additional metadata as JSON string
        build_tree: Whether to build RAPTOR tree after ingestion (default: True)
        summary_llm: LLM model to use for summarization
        vector_index: Vector index configuration as JSON string
        upsert_mode: How to handle duplicate documents
        x_dataset_id: Alternative dataset ID via header

    Returns:
        Processing result with document ID and processing status
    """
    # Validate file format
    file = await require_markdown_file(file)

    # Create dataset controller for validation and enhancement
    dataset_controller = DatasetController(request)

    # Validate dataset_id first (optional step for better UX)
    try:
        validation = await dataset_controller.validate_dataset(dataset_id)
        if not validation.get("valid", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid dataset ID: {dataset_id}"
            )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception:
        pass  # Don't fail the upload if validation fails, just proceed

    payload_dict = {
        "dataset_id": dataset_id,
        "source": source,
        "tags": tags,
        "extra_meta": parse_json_opt("extra_meta", extra_meta),
        "build_tree": build_tree,
        "summary_llm": summary_llm,
        "vector_index": parse_json_opt("vector_index", vector_index),
        "upsert_mode": upsert_mode,
    }

    payload_dict = {k: v for k, v in payload_dict.items() if v is not None}

    payload_json = json.dumps(payload_dict, ensure_ascii=False)

    result = await DocumentController(request).ingest_markdown(
        file=file,
        payload=payload_json,
        x_dataset_id=x_dataset_id,
    )

    # Enhance the result with dataset information
    if isinstance(result, dict) and "dataset_id" in result:
        try:
            dataset_info = await dataset_controller.get_dataset(result["dataset_id"])
            result["dataset_info"] = {
                "name": dataset_info.get("name", result["dataset_id"]),
                "document_count": dataset_info.get("document_count", 0),
            }
        except Exception:
            pass  # Don't fail if we can't get dataset info

    return result


@router.post("/retrieve")
async def retrieve(body: RetrieveBody, request: Request):
    container = request.app.state.container
    uow = container.make_uow()
    async with uow:
        repo = RetrievalRepo(uow)
        result = await _SERVICE.retrieve(body, repo=repo)
        return result


class AnswerBody(RetrieveBody):
    answer_model: Literal["DeepSeek-V3", "GPT-4o-mini", "Gemini-2.5-Flash", "Claude-3.5-Haiku"] = (
        "DeepSeek-V3"
    )
    temperature: float = 0.3
    max_tokens: int = 4000
    stream: bool = False


@router.post("/answer")
async def answer_query(body: AnswerBody, request: Request):
    container = request.app.state.container
    uow = container.make_uow()
    async with uow:
        repo = RetrievalRepo(uow)
        result = await _ANSWER.answer(body, repo=repo)
        return result
