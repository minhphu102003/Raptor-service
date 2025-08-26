from typing import Iterable, List


def build_leaf_row(leaf_id: str, tree_id: str, text: str, chunk_id: str) -> dict:
    return {
        "node_id": leaf_id,
        "tree_id": tree_id,
        "level": 0,
        "kind": "leaf",
        "text": text,
        "meta": {"chunk_id": chunk_id},
    }


def build_summary_node_row(node_id: str, tree_id: str, level: int, summary: str) -> dict:
    return {
        "node_id": node_id,
        "tree_id": tree_id,
        "level": level,
        "kind": "summary",
        "text": summary,
        "meta": {},
    }


def build_edges(parent_id: str, child_ids: Iterable[str]) -> List[dict]:
    return [{"parent_id": parent_id, "child_id": cid} for cid in child_ids]


def build_links(node_id: str, chunk_ids: List[str]) -> List[dict]:
    return [{"node_id": node_id, "chunk_id": cid, "rank": i} for i, cid in enumerate(chunk_ids)]


def build_embed_row(
    node_id: str, dataset_id: str, model: str, dim: int, v: List[float], tree_id: str, level: int
) -> dict:
    return {
        "id": f"tree_node::{node_id}",
        "dataset_id": dataset_id,
        "owner_type": "tree_node",
        "owner_id": node_id,
        "model": model,
        "dim": dim,
        "v": v,
        "meta": {"tree_id": tree_id, "level": level},
    }
