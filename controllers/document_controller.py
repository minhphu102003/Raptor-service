import logging

from fastapi import HTTPException, Request, status
from pydantic import ValidationError

from interfaces_adaptor.http.dtos import IngestMarkdownPayload
from services.document_service import DocumentService

storage_log = logging.getLogger("storage")


class DocumentController:
    def __init__(self, request: Request):
        self.request = request
        self.container = request.app.state.container
        self.service = DocumentService(self.container)

    async def ingest_markdown(self, file, payload: str, x_dataset_id: str | None):
        try:
            pl = IngestMarkdownPayload.model_validate_json(payload)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.errors(),
            )

        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File upload là bắt buộc"
            )

        return await self.service.ingest_markdown(file_bytes, pl, x_dataset_id)
