from dataclasses import dataclass
from typing import Optional


@dataclass
class IngestResult:
    doc_id: str
    chunks: int
    job_id: Optional[str] = None
    tree_id: Optional[str] = None
