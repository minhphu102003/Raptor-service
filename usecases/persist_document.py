from interfaces_adaptor.ports import IDocumentRepository, IFileSource, IUnitOfWork

from .types import PersistDocumentCmd, PersistDocumentResult


class PersistDocumentUseCase:
    def __init__(
        self, *, file_source: IFileSource, doc_repo: IDocumentRepository, uow: IUnitOfWork
    ):
        self.file_source = file_source
        self.doc_repo = doc_repo
        self.uow = uow

    async def execute(self, cmd: PersistDocumentCmd) -> PersistDocumentResult:
        source_uri, checksum = await self.file_source.persist_and_checksum(
            cmd.file_bytes, cmd.file_url
        )

        async with self.uow:
            if cmd.upsert_mode == "skip_duplicates":
                existed = await self.doc_repo.find_by_checksum(cmd.dataset_id, checksum)
                if existed:
                    return PersistDocumentResult(
                        existed.doc_id, existed.dataset_id, existed.source, checksum
                    )

            await self.doc_repo.save_document(
                {
                    "doc_id": cmd.doc_id,
                    "dataset_id": cmd.dataset_id,
                    "source": cmd.source or source_uri,
                    "tags": cmd.tags,
                    "extra_meta": cmd.extra_meta,
                    "checksum": checksum,
                }
            )
            return PersistDocumentResult(
                cmd.doc_id, cmd.dataset_id, cmd.source or source_uri, checksum
            )
