from typing import Optional

from sqlalchemy.exc import IntegrityError as SAIntegrityError

try:
    import asyncpg
except Exception:
    asyncpg = None

from interfaces_adaptor.ports import IDocumentRepository, IFileSource, IUnitOfWork

from .types import PersistDocumentCmd, PersistDocumentResult


class DuplicateIdError(Exception):
    def __init__(self, doc_id: str):
        super().__init__(f"Document with id '{doc_id}' already exists.")
        self.doc_id = doc_id


class PersistDocumentUseCase:
    def __init__(
        self, *, file_source: IFileSource, doc_repo: IDocumentRepository, uow: IUnitOfWork
    ):
        self.file_source = file_source
        self.doc_repo = doc_repo
        self.uow = uow

    async def execute(self, cmd: PersistDocumentCmd) -> PersistDocumentResult:
        if not cmd.file_bytes:
            raise ValueError("file_bytes is required")

        source_uri, checksum = await self.file_source.persist_and_checksum(cmd.file_bytes)

        # Raise bên trong context để __aexit__ rollback & close phiên
        try:
            async with self.uow:
                await self.doc_repo.save_document(
                    {
                        "doc_id": cmd.doc_id,
                        "dataset_id": cmd.dataset_id,
                        "source": cmd.source or source_uri,
                        "tags": cmd.tags,
                        "extra_meta": cmd.extra_meta,
                        "checksum": checksum,
                        "text": cmd.text,
                    }
                )
        except SAIntegrityError as e:
            # Postgres unique violation: SQLSTATE 23505
            orig = getattr(e, "orig", None)
            sqlstate: Optional[str] = getattr(orig, "sqlstate", None)
            is_unique_violation = sqlstate == "23505" or (
                asyncpg and isinstance(orig, asyncpg.UniqueViolationError)
            )
            if is_unique_violation:
                raise DuplicateIdError(cmd.doc_id) from e
            raise  # các lỗi integrity khác: ném tiếp

        return PersistDocumentResult(cmd.doc_id, cmd.dataset_id, cmd.source or source_uri, checksum)
