from dataclasses import dataclass
from typing import Optional


@dataclass
class IngestResult:
    doc_id: str
    chunks: int
    job_id: Optional[str] = None
    tree_id: Optional[str] = None


@dataclass
class PersistDocumentCmd:
    dataset_id: str
    doc_id: str
    file_bytes: Optional[bytes]
    source: Optional[str]
    tags: Optional[list[str]]
    extra_meta: Optional[dict]
    upsert_mode: str
    text: Optional[str] = None


@dataclass
class PersistDocumentResult:
    doc_id: str
    dataset_id: str
    source_uri: str
    checksum: str


@dataclass
class NaiveChunkConfig:
    chunk_size_tokens: int = 800
    chunk_overlap_tokens: int = 100
    max_chunks: Optional[int] = None
    tokenizer_encoding: str = "cl100k_base"


@dataclass
class EmbedAndIndexCmd:
    doc_id: str
    dataset_id: str
    text: str
    model: str
    method: str
    output_dimension: int
