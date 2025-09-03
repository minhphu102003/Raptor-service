import logging
import os
from statistics import median
import time
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from utils.packing import count_tokens_total

load_dotenv()

logger = logging.getLogger("raptor.retrieve")


def _ms_since(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000.0, 1)


class RetrieveBody(BaseModel):
    dataset_id: str
    query: str
    mode: Literal["collapsed", "traversal"] = "collapsed"
    top_k: int = 8
    expand_k: int = 5
    levels_cap: int = 0
    use_reranker: bool = False
    reranker_model: Optional[str] = None
    byok_voyage_api_key: Optional[str] = None


class RetrievalService:
    def __init__(self, rewrite_svc, embed_svc, reranker_svc=None):
        self.rewrite = rewrite_svc
        self.embed = embed_svc
        self.reranker = reranker_svc

    async def retrieve(self, body: RetrieveBody, *, repo) -> dict:
        t_total = time.perf_counter()
        base_extra = {
            "dataset": body.dataset_id,
            "mode": body.mode,
            "top_k": body.top_k,
            "expand_k": body.expand_k,
            "levels_cap": body.levels_cap,
        }
        logger.info(
            "retrieve.start",
            extra={"span": "retrieve.start", "ms": 0, "extra": {}, **base_extra},
        )
        api_key: str | None = os.getenv("VOYAGEAI_KEY")

        t = time.perf_counter()
        q_tok_before = (
            count_tokens_total([body.query], model="voyage-context-3", api_key=api_key)
            if api_key
            else 0
        )
        q_norm = await self.rewrite.normalize_query(
            body.query,
            byok_voyage_key=body.byok_voyage_api_key,
        )
        q_tok_after = (
            count_tokens_total([q_norm], model="voyage-context-3", api_key=api_key)
            if api_key
            else 0
        )
        logger.info(
            "rewrite.done",
            extra={
                "span": "rewrite",
                "ms": _ms_since(t),
                "extra": {
                    "tokens_before": q_tok_before,
                    "tokens_after": q_tok_after,
                    "changed": body.query.strip() != q_norm.strip(),
                },
                **base_extra,
            },
        )

        t = time.perf_counter()
        q_vec = await self.embed.embed_query(
            q_norm, byok_voyage_key=body.byok_voyage_api_key, dim=1024
        )
        logger.info(
            "embed.done",
            extra={
                "span": "embed",
                "ms": _ms_since(t),
                "extra": {"dim": len(q_vec)},
                **base_extra,
            },
        )

        if body.mode == "collapsed":
            # 1) tìm summary/root nodes gần nhất
            t = time.perf_counter()
            nodes = await repo.search_summary_nodes(
                dataset_id=body.dataset_id, q_vec=q_vec, limit=body.expand_k
            )
            node_ids = [n["node_id"] for n in nodes]
            top_dist = nodes[0]["dist"] if nodes else None
            logger.info(
                "collapsed.nodes",
                extra={
                    "span": "collapsed.nodes",
                    "ms": _ms_since(t),
                    "extra": {"n": len(nodes), "top_dist": top_dist},
                    **base_extra,
                },
            )
            # 2) expand xuống chunks và xếp hạng theo q_vec
            t = time.perf_counter()
            chunks = await repo.gather_leaf_chunks(
                dataset_id=body.dataset_id, node_ids=node_ids, q_vec=q_vec, top_k=body.top_k
            )
            dists = [c.get("dist") for c in chunks if "dist" in c]
            logger.info(
                "collapsed.chunks",
                extra={
                    "span": "collapsed.chunks",
                    "ms": _ms_since(t),
                    "extra": {
                        "n": len(chunks),
                        "best": (min(dists) if dists else None),
                        "median": (median(dists) if dists else None),
                    },
                    **base_extra,
                },
            )
        else:
            t = time.perf_counter()
            chunks = await repo.traversal_retrieve(
                dataset_id=body.dataset_id,
                q_vec=q_vec,
                top_k=body.top_k,
                levels_cap=body.levels_cap,
            )
            logger.info(
                "traversal.chunks",
                extra={
                    "span": "traversal",
                    "ms": _ms_since(t),
                    "extra": {"n": len(chunks)},
                    **base_extra,
                },
            )

        if body.use_reranker and self.reranker:
            t = time.perf_counter()
            before = len(chunks)
            chunks = await self.reranker.rerank(chunks, body.reranker_model, q_norm)
            logger.info(
                "rerank.done",
                extra={
                    "span": "rerank",
                    "ms": _ms_since(t),
                    "extra": {"before": before, "after": len(chunks), "model": body.reranker_model},
                    **base_extra,
                },
            )

        logger.info(
            "retrieve.done",
            extra={
                "span": "retrieve.done",
                "ms": _ms_since(t_total),
                "extra": {"returned": len(chunks)},
                **base_extra,
            },
        )
        return {"code": 200, "data": chunks}
