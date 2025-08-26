import os
import uuid

from interfaces_adaptor.http.dtos import IngestMarkdownPayload

DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "default")


def gen_doc_id() -> str:
    return uuid.uuid4().hex


def resolve_dataset_id(pl: IngestMarkdownPayload | None, x_dataset_id: str | None) -> str:
    return (pl.dataset_id if pl and pl.dataset_id else x_dataset_id) or DEFAULT_DATASET_ID


def make_leaf_id(tree_id: str, idx: int) -> str:
    return f"{tree_id}::leaf::{idx:06d}"


def make_node_id(tree_id: str, level: int, group_idx: int) -> str:
    return f"{tree_id}::L{level}::{group_idx}::{uuid.uuid4().hex[:6]}"
