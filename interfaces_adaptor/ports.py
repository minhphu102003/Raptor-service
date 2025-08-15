from typing import Any, Optional, Protocol, Sequence


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


class ITreeRepository(Protocol):
    def save_tree(self, tree: dict) -> str: ...


class IQueue(Protocol):
    def enqueue(self, job_name: str, payload: dict) -> str: ...


class IFileSource(Protocol):
    async def load_markdown(self, file_bytes: Optional[bytes], file_url: Optional[str]) -> str: ...
