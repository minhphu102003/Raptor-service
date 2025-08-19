# interfaces_adaptor/ports.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, Sequence, Type


# ----- DTOs -----
@dataclass
class ChunkDTO:
    chunk_id: str
    doc_id: str
    dataset_id: str
    index: int
    text: str
    token_count: int | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    source_uri: str | None = None
    extra_meta: dict | None = None


@dataclass
class EmbeddingDTO:
    emb_id: str  # ví dụ: f"chunk::{chunk_id}"
    dataset_id: str
    owner_type: str  # "chunk" | "tree_node"
    owner_id: str  # chunk_id / node_id
    model: str  # "voyage-3" ...
    dim: int  # 1024
    vector: List[float]  # len == dim
    extra_meta: dict | None = None


# ----- Low-level providers (tuỳ bạn có dùng) -----
class IFileSource(Protocol):
    async def load_markdown(self, file_bytes: Optional[bytes]) -> str: ...
    async def persist_and_checksum(self, file_bytes: Optional[bytes]) -> tuple[str, str]: ...
    async def read(self, source_uri: str) -> bytes: ...


class IChunker(Protocol):
    async def split(self, text: str) -> list[ChunkDTO]: ...


class IEmbedder(Protocol):
    dim: int

    async def embed(self, texts: Sequence[str], *, batch_size: int = 64) -> list[list[float]]: ...
    async def embed_chunks(
        self, texts: Sequence[str], *, model: str, output_dimension: int, method: str
    ) -> list[list[float]]: ...


# (tuỳ chọn) external vector index (Qdrant/Milvus, …)
class IVectorIndex(Protocol):
    name: str
    namespace: Optional[str]

    def upsert(
        self, ids: Sequence[str], vectors: Sequence[Sequence[float]], meta: Sequence[dict[str, Any]]
    ) -> None: ...
    async def bulk_upsert(
        self, *, dim: int, model: str, method: str, items: Iterable[tuple[str, list[float]]]
    ) -> int: ...


# ----- Repositories (DB) -----
class IDocumentRepository(Protocol):
    async def save_document(self, doc: dict) -> None: ...
    async def get_document(self, doc_id: str) -> Optional[Any]: ...
    async def find_by_checksum(self, dataset_id: str, checksum: str) -> Optional[Any]: ...


class IChunkRepository(Protocol):
    async def bulk_upsert(self, chunks: Iterable[ChunkDTO]) -> int: ...


class IEmbeddingRepository(Protocol):
    async def bulk_upsert(self, embs: Iterable[EmbeddingDTO]) -> int: ...


class ITreeRepository(Protocol):
    async def save_tree(self, tree: dict) -> str: ...


# ----- UoW -----
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


class ChunkFnProvider(Protocol):
    def build(self) -> Callable[[str], List[str]]: ...
