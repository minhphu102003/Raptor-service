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
    file_url: Optional[str]
    source: Optional[str]
    tags: Optional[list[str]]
    extra_meta: Optional[dict]
    upsert_mode: str


@dataclass
class PersistDocumentResult:
    doc_id: str
    dataset_id: str
    source_uri: str
    checksum: str
