from typing import Any, Optional, Protocol, Sequence, Type


class IEmbedder(Protocol):
    dim: int
    space: str
    normalized: bool

    async def embed(self, texts: Sequence[str], *, batch_size: int = 64) -> list[list[float]]: ...


class IChatLLM(Protocol):
    async def summarize(self, text: str, *, max_tokens: int, temperature: float) -> str: ...


class IVectorIndex(Protocol):
    name: str
    namespace: Optional[str]

    def upsert(
        self, ids: Sequence[str], vectors: Sequence[Sequence[float]], meta: Sequence[dict[str, Any]]
    ) -> None: ...


class IDocumentRepository(Protocol):
    def save_document(self, doc: dict) -> None: ...
    def save_chunks(self, chunks: list[dict]) -> None: ...
    async def get_document(self, doc_id: str) -> Optional[Any]: ...
    async def find_by_checksum(self, dataset_id: str, checksum: str) -> Optional[Any]: ...


class ITreeRepository(Protocol):
    def save_tree(self, tree: dict) -> str: ...


class IQueue(Protocol):
    def enqueue(self, job_name: str, payload: dict) -> str: ...


class IFileSource(Protocol):
    async def load_markdown(self, file_bytes: Optional[bytes]) -> str: ...
    async def persist_and_checksum(self, file_bytes: Optional[bytes]) -> tuple[str, str]: ...
    async def read(self, source_uri: str) -> bytes: ...


class IUnitOfWork(Protocol):
    async def __aenter__(self) -> "IUnitOfWork": ...
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[Any],
    ) -> None: ...

    async def begin(self) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...

    @property
    def session(self) -> Any: ...
