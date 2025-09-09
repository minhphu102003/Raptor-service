import logging
from statistics import median
import time
from typing import Literal, Optional

from pydantic import BaseModel, ValidationInfo, field_validator

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

    # Add validation logging
    @field_validator("*")
    @classmethod
    def log_validation(cls, v, info: ValidationInfo):
        # This will log each field during validation
        logger.info(f"Validating field {info.field_name}: {v} (type: {type(v)})")
        return v


class RetrievalService:
    def __init__(self, embed_svc, reranker_svc=None):
        self.embed = embed_svc
        self.reranker = reranker_svc

    async def retrieve(self, body: RetrieveBody, *, repo) -> dict:
        logger.info(f"RetrievalService.retrieve called with body: {body.dict()}")
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

        # Use the original query directly instead of rewriting
        q_norm = body.query
        logger.debug(f"Using original query: {q_norm}")

        # Trace logging for embedding generation
        t = time.perf_counter()
        logger.debug(f"Starting embedding generation for query: {q_norm}")
        q_vec_result = await self.embed.embed_queries([q_norm])
        # Extract the first (and only) embedding from the result
        q_vec = q_vec_result[0] if q_vec_result else []
        logger.debug(f"Embedding generation completed. Vector dimension: {len(q_vec)}")
        logger.info(
            "embed.done",
            extra={
                "span": "embed",
                "ms": _ms_since(t),
                "extra": {"dim": len(q_vec) if q_vec else 0},
                **base_extra,
            },
        )

        if body.mode == "collapsed":
            # 1) tìm summary/root nodes gần nhất
            t = time.perf_counter()
            db_t = time.perf_counter()  # Track database query time separately
            logger.debug("Starting search for summary nodes (collapsed mode)")
            nodes = await repo.search_summary_nodes(
                dataset_id=body.dataset_id, q_vec=q_vec, limit=body.expand_k
            )
            db_time = _ms_since(db_t)  # Database query time
            node_ids = [n["node_id"] for n in nodes]
            top_dist = nodes[0]["dist"] if nodes else None
            logger.debug(f"Found {len(nodes)} summary nodes. Top distance: {top_dist}")
            logger.info(
                "collapsed.nodes",
                extra={
                    "span": "collapsed.nodes",
                    "ms": _ms_since(t),
                    "extra": {"n": len(nodes), "top_dist": top_dist, "db_time_ms": db_time},
                    **base_extra,
                },
            )
            # 2) expand xuống chunks và xếp hạng theo q_vec
            t = time.perf_counter()
            db_t = time.perf_counter()  # Track database query time separately
            logger.debug(f"Starting leaf chunk gathering for {len(node_ids)} nodes")
            chunks = await repo.gather_leaf_chunks(
                dataset_id=body.dataset_id, node_ids=node_ids, q_vec=q_vec, top_k=body.top_k
            )
            db_time = _ms_since(db_t)  # Database query time
            dists = [c.get("dist") for c in chunks if "dist" in c]
            logger.debug(f"Gathered {len(chunks)} leaf chunks")
            logger.info(
                "collapsed.chunks",
                extra={
                    "span": "collapsed.chunks",
                    "ms": _ms_since(t),
                    "extra": {
                        "n": len(chunks),
                        "best": (min(dists) if dists else None),
                        "median": (median(dists) if dists else None),
                        "db_time_ms": db_time,
                    },
                    **base_extra,
                },
            )
        else:
            t = time.perf_counter()
            db_t = time.perf_counter()  # Track database query time separately
            logger.debug("Starting traversal retrieval")
            chunks = await repo.traversal_retrieve(
                dataset_id=body.dataset_id,
                q_vec=q_vec,
                top_k=body.top_k,
                levels_cap=body.levels_cap,
            )
            db_time = _ms_since(db_t)  # Database query time
            logger.debug(f"Traversal retrieval completed. Found {len(chunks)} chunks")
            logger.info(
                "traversal.chunks",
                extra={
                    "span": "traversal",
                    "ms": _ms_since(t),
                    "extra": {"n": len(chunks), "db_time_ms": db_time},
                    **base_extra,
                },
            )

        if body.use_reranker and self.reranker:
            t = time.perf_counter()
            logger.debug(f"Starting reranking of {len(chunks)} chunks")
            before = len(chunks)
            chunks = await self.reranker.rerank(chunks, body.reranker_model, q_norm)
            logger.debug(f"Reranking completed. Chunks before: {before}, after: {len(chunks)}")
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
