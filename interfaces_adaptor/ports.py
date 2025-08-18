from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence, Type


@dataclass
class Chunk:
    id: str
    order: int
    text: str
    meta: Dict[str, Any]


class IChunker(Protocol):
    def chunk(self, full_text: str) -> List[Chunk]: ...


class ChunkFnProvider(Protocol):
    def build(self) -> Callable[[str], List[str]]: ...


class IEmbeddingClient(Protocol):
    async def embed_documents(
        self,
        texts: List[str],
        model: str,
        input_type: str,
        output_dimension: Optional[int],
        output_dtype: Optional[str],
    ) -> List[List[float]]: ...
    async def embed_contextualized(
        self,
        chunks: List[str],
        model: str,
        output_dimension: Optional[int],
        output_dtype: Optional[str],
    ) -> List[List[float]]: ...


class IVectorIndex(Protocol):
    async def upsert(
        self, items: List[Dict[str, Any]], namespace: str, upsert_mode: str = "upsert"
    ) -> Dict[str, Any]: ...


class IRaptorBuilder(Protocol):
    async def build(self, chunks: List[Chunk]) -> str: ...


class IDeduper(Protocol):
    def filter(self, chunks: List[Chunk]) -> List[Chunk]: ...


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
