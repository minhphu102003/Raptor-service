from __future__ import annotations

from typing import Callable, TypedDict

from fastapi import FastAPI, HTTPException

from app.api_schemas import BuildRequest, BuildResponse  # , RetrieveRequest (nếu dùng)
from app.settings import settings  # noqa: F401  # (tránh cảnh báo unused tạm thời)
from raptor.raptor_core import build_tree  # hoặc raptor.core tuỳ tên file của bạn


class Node(TypedDict, total=False):
    text: str
    embedding: list[float]
    is_summary: bool


app = FastAPI(title="RAPTOR Service")


@app.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}


@app.post("/v1/trees:build", response_model=BuildResponse)
def trees_build(req: BuildRequest) -> BuildResponse:
    # TODO: validate: all len(emb) == req.embedding_spec.embedding_dim
    nodes: list[Node] = [{"text": n.text, "embedding": n.embedding or []} for n in req.nodes]

    SummarizeFn = Callable[[list[str], int], str]
    EmbedFn = Callable[[str], list[float]]

    def summarize_fn(texts: list[str], max_tokens: int) -> str:
        return "\n".join(texts)[:2048]

    def embed_fn(text: str) -> list[float]:
        raise HTTPException(status_code=501, detail="auto-embed not configured")

    out_nodes: list[Node] = build_tree(
        chunks=nodes,
        params=req.params.model_dump(),
        summarize_fn=summarize_fn,
        embed_fn=embed_fn,
        random_state=42,
    )
    # TODO: persist nodes/edges, index vectors (pgvector/milvus)

    return BuildResponse(
        tree_id=req.tree_id or f"{req.dataset_id}.v1",
        dataset_id=req.dataset_id,
        stats={
            "input_chunks": len(req.nodes),
            "levels": 0,
            "nodes_total": len(out_nodes),
            "summary_nodes": len(out_nodes) - len(req.nodes),
            "embedding_dim": req.embedding_spec.embedding_dim,
        },
        root_node_id="n_root",
        vector_index={"indexed_sets": ["leaf"], "space": req.embedding_spec.space},
    )
