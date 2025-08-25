import json
from typing import Optional, Type, TypeVar

from fastapi import HTTPException, status
from pydantic import TypeAdapter, ValidationError

T = TypeVar("T")


def parse_json_opt(field_name: str, raw: Optional[str]) -> Optional[object]:
    if raw is None or raw == "":
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trường '{field_name}' phải là JSON hợp lệ.",
        )


def parse_json_typed(field_name: str, raw: Optional[str], model: Type[T]) -> Optional[T]:
    if raw is None or raw == "":
        return None
    try:
        adapter = TypeAdapter(model)
        return adapter.validate_json(raw)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trường '{field_name}' phải là JSON theo schema {getattr(model, '__name__', model)}.",
        )
