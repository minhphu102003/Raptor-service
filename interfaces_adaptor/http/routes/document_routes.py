import json
from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile, status

from constants.enum import SummarizeModel
from interfaces_adaptor.http.controllers.document_controller import DocumentController
from interfaces_adaptor.http.dependencies.files import require_markdown_file

router = APIRouter()


def _parse_json_opt(field_name: str, raw: Optional[str]):
    if raw is None or raw == "":
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trường '{field_name}' phải là JSON hợp lệ.",
        )


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
        "extra_meta": _parse_json_opt("extra_meta", extra_meta),
        "build_tree": build_tree,
        "summary_llm": summary_llm,
        "vector_index": _parse_json_opt("vector_index", vector_index),
        "upsert_mode": upsert_mode,
        "byok": {
            "openai_api_key": byok_openai_api_key,
            "azure_openai": _parse_json_opt("byok_azure_openai", byok_azure_openai),
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
