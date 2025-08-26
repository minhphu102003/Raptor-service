from dataclasses import Field
import json
from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, Header, Request, UploadFile, status
from openai import BaseModel

from constants.enum import SummarizeModel
from controllers.document_controller import DocumentController
from interfaces_adaptor.http.dependencies.files import require_markdown_file
from repositories.retrieval_repo import RetrievalRepo
from services.embedding_query_service import EmbeddingService
from services.fpt_llm.client import FPTLLMClient
from services.query_rewrite_service import QueryRewriteService
from services.retrieval_service import RetrievalService
from services.voyage.voyage_client import VoyageEmbeddingClientAsync
from utils.json import parse_json_opt

router = APIRouter()

_FPT = FPTLLMClient(model="DeepSeek-V3")
_VOY = VoyageEmbeddingClientAsync(model="voyage-context-3", out_dim=1024)

_REWRITE = QueryRewriteService(fpt_client=_FPT)
_EMBED = EmbeddingService(voyage_client_async=_VOY)
_SERVICE = RetrievalService(rewrite_svc=_REWRITE, embed_svc=_EMBED)


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
    byok_openai_api_key: Annotated[Optional[str], Form()] = None,
    byok_azure_openai: Annotated[Optional[str], Form()] = None,
    byok_cohere_api_key: Annotated[Optional[str], Form()] = None,
    byok_huggingface_token: Annotated[Optional[str], Form()] = None,
    byok_dashscope_api_key: Annotated[Optional[str], Form()] = None,
    byok_gemini_api_key: Annotated[Optional[str], Form()] = None,
    byok_voyage_api_key: Annotated[Optional[str], Form()] = None,
    x_dataset_id: Annotated[Optional[str], Header(alias="X-Dataset-Id")] = None,
):
    file = await require_markdown_file(file)

    payload_dict = {
        "dataset_id": dataset_id,
        "source": source,
        "tags": tags,
        "extra_meta": parse_json_opt("extra_meta", extra_meta),
        "build_tree": build_tree,
        "summary_llm": summary_llm,
        "vector_index": parse_json_opt("vector_index", vector_index),
        "upsert_mode": upsert_mode,
        "byok": {
            "openai_api_key": byok_openai_api_key,
            "azure_openai": parse_json_opt("byok_azure_openai", byok_azure_openai),
            "cohere_api_key": byok_cohere_api_key,
            "huggingface_token": byok_huggingface_token,
            "dashscope_api_key": byok_dashscope_api_key,
            "gemini_api_key": byok_gemini_api_key,
            "voyage_api_key": byok_voyage_api_key,
        },
    }

    payload_dict["byok"] = {k: v for k, v in payload_dict["byok"].items() if v is not None}
    payload_dict = {k: v for k, v in payload_dict.items() if v is not None}

    payload_json = json.dumps(payload_dict, ensure_ascii=False)

    return await DocumentController(request).ingest_markdown(
        file=file,
        payload=payload_json,
        x_dataset_id=x_dataset_id,
    )


class RetrieveBody(BaseModel):
    dataset_id: str
    query: str
    mode: Literal["collapsed", "traversal"] = "collapsed"
    top_k: int = 8
    expand_k: int = 5
    levels_cap: int = 0
    use_reranker: bool = False
    reranker_model: Optional[str] = None
    byok_voyage_api_key: Optional[str] = None


@router.post("/retrieve")
async def retrieve(body: RetrieveBody, request: Request):
    container = request.app.state.container
    uow = container.make_uow()
    async with uow:
        repo = RetrievalRepo(uow)
        result = await _SERVICE.retrieve(body, repo=repo)
        return result
