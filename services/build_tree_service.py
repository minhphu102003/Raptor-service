import asyncio
import logging
import time
from typing import Any, Dict, List, Tuple
import uuid

from sqlalchemy.exc import DBAPIError, IntegrityError

logger = logging.getLogger("raptor")


class RaptorBuildService:
    def __init__(self, *, embedder, clusterer, summarizer, tree_repo, emb_repo, chunk_repo):
        self.embedder = embedder
        self.clusterer = clusterer
        self.summarizer = summarizer
        self.tree_repo = tree_repo
        self.emb_repo = emb_repo
        self.chunk_repo = chunk_repo
        self._last_embed_ts = 0.0

    async def build_from_memory_pairs(
        self,
        *,
        doc_id: str,
        dataset_id: str,
        chunk_items: List[dict],
        vectors: List[List[float]],
        params: Dict[str, Any] | None = None,
    ) -> str:
        params = params or {}
        tree_id = await self._init_tree(doc_id, dataset_id, params)

        leaf_ids, node2chunk_ids = await self._prepare_leaves(tree_id, chunk_items)

        rpm_limit = int(params.get("rpm_limit", 3))
        min_interval = 60.0 / max(1, rpm_limit)
        self._ensure_last_ts(min_interval)

        llm_conc = int(params.get("llm_concurrency", 3))
        sem = asyncio.Semaphore(max(1, llm_conc))

        current_ids, current_vecs, current_texts = (
            leaf_ids,
            list(vectors),
            [it["text"] for it in chunk_items],
        )
        level = 0

        while len(current_ids) > 1:
            t0 = time.perf_counter()

            groups = self.clusterer.fit_predict(
                current_vecs,
                min_k=int(params.get("min_k", 2)),
                max_k=int(params.get("max_k", 50)),
                verbose=True,
            )
            logger.info(
                "[RAPTOR] L%d clusters=%d sizes=%s score=%s method=%s",
                level + 1,
                len(groups),
                [len(ix) for ix in groups],
                getattr(self.clusterer, "last_info", {}).get("best_score"),
                getattr(self.clusterer, "last_info", {}).get("criterion", "BIC"),
            )

            summaries, group_pack = await self._summarize_groups(
                groups, current_ids, current_texts, params, sem, level
            )

            vecs = await self._embed_with_throttle(summaries, min_interval, level)

            current_ids, current_vecs, current_texts = await self._persist_level(
                tree_id, dataset_id, group_pack, summaries, vecs, node2chunk_ids, level
            )

            logger.info(
                "[RAPTOR] L%d commit nodes=%d edges=%d ms=%.1f",
                level + 1,
                len(current_ids),
                len(current_ids) - 1,
                (time.perf_counter() - t0) * 1e3,
            )
            level += 1

        logger.info("[RAPTOR] done tree_id=%s levels=%d", tree_id, level)
        return tree_id

    async def _init_tree(self, doc_id: str, dataset_id: str, params: Dict[str, Any]) -> str:
        tree_id = await self.tree_repo.create_tree(
            doc_id=doc_id, dataset_id=dataset_id, params=params
        )
        logger.info(
            "[RAPTOR] create_tree tree_id=%s doc_id=%s dataset_id=%s", tree_id, doc_id, dataset_id
        )
        return tree_id

    async def _prepare_leaves(
        self, tree_id: str, chunk_items: List[dict]
    ) -> Tuple[List[str], Dict[str, List[str]]]:
        leaf_rows, link_rows, leaf_ids = [], [], []
        chunk2leaf, node2chunk_ids = {}, {}

        for i, it in enumerate(chunk_items):
            leaf_id = f"{tree_id}::leaf::{i:06d}"
            leaf_rows.append(
                {
                    "node_id": leaf_id,
                    "tree_id": tree_id,
                    "level": 0,
                    "kind": "leaf",
                    "text": it["text"],
                    "meta": {"chunk_id": it["id"]},
                }
            )
            link_rows.append({"node_id": leaf_id, "chunk_id": it["id"], "rank": 0})
            logger.info("[RAPTOR] chunk_id=%s text=%s", it["id"], it["text"])
            leaf_ids.append(leaf_id)
            chunk2leaf[it["id"]] = leaf_id
            node2chunk_ids[leaf_id] = [it["id"]]

        await self.tree_repo.add_nodes(tree_id, leaf_rows)
        await self.tree_repo.link_node_chunks(link_rows)
        return leaf_ids, node2chunk_ids

    async def _summarize_groups(
        self,
        groups: List[List[int]],
        current_ids: List[str],
        current_texts: List[str],
        params: Dict[str, Any],
        sem: asyncio.Semaphore,
        level: int,
    ) -> Tuple[List[str], List[Tuple[int, List[str], List[str]]]]:
        async def _summarize(texts: List[str], max_tokens: int) -> str:
            async with sem:
                return await self.summarizer.summarize_cluster(texts, max_tokens=max_tokens)

        tasks, group_pack = [], []
        for gi, idxs in enumerate(groups):
            member_ids = [current_ids[i] for i in idxs]
            member_texts = [current_texts[i] for i in idxs]
            group_pack.append((gi, member_ids, member_texts))
            tasks.append(_summarize(member_texts, int(params.get("max_tokens", 4048))))
            logger.debug(
                "[RAPTOR] L%d G%d members=%d ids=%s", level + 1, gi, len(member_ids), member_ids
            )

        summaries = await asyncio.gather(*tasks)
        return summaries, group_pack

    async def _embed_with_throttle(
        self, texts: List[str], min_interval: float, level: int
    ) -> List[List[float]]:
        now = time.perf_counter()
        sleep_for = (self._last_embed_ts + min_interval) - now
        if sleep_for > 0:
            await asyncio.sleep(sleep_for)

        self._last_embed_ts = time.perf_counter()
        vecs = await self.embedder.embed_docs(texts)
        logger.info(
            "[RAPTOR] L%d batch-embed n=%d ms=%.1f",
            level + 1,
            len(texts),
            (time.perf_counter() - self._last_embed_ts) * 1e3,
        )
        return vecs

    async def _persist_level(
        self,
        tree_id: str,
        dataset_id: str,
        group_pack: List[Tuple[int, List[str], List[str]]],
        summaries: List[str],
        vecs: List[List[float]],
        node2chunk_ids: Dict[str, List[str]],
        level: int,
    ) -> Tuple[List[str], List[List[float]], List[str]]:
        node_rows, edge_rows, link_rows, emb_rows = [], [], [], []
        node_ids_for_level = []

        for (gi, member_ids, member_texts), summary, vec in zip(group_pack, summaries, vecs):
            node_id = f"{tree_id}::L{level + 1}::{gi}::{uuid.uuid4().hex[:6]}"
            node_ids_for_level.append(node_id)

            node_rows.append(
                {
                    "node_id": node_id,
                    "tree_id": tree_id,
                    "level": level + 1,
                    "kind": "summary",
                    "text": summary,
                    "meta": {},
                }
            )

            edge_rows.extend([{"parent_id": node_id, "child_id": cid} for cid in member_ids])

            agg_chunk_ids = self._aggregate_chunks(member_ids, node2chunk_ids)
            link_rows.extend(
                [
                    {"node_id": node_id, "chunk_id": cid, "rank": rank}
                    for rank, cid in enumerate(agg_chunk_ids)
                ]
            )
            node2chunk_ids[node_id] = agg_chunk_ids

            emb_rows.append(
                {
                    "id": f"tree_node::{node_id}",
                    "dataset_id": dataset_id,
                    "owner_type": "tree_node",
                    "owner_id": node_id,
                    "model": self.embedder.model_name,
                    "dim": self.embedder.dim,
                    "v": vec,
                    "meta": {"tree_id": tree_id, "level": level + 1},
                }
            )

        if len(node_ids_for_level) == 1:
            node_rows[0]["kind"] = "root"
            node_rows[0]["meta"]["is_root"] = True
            logger.info(
                "[RAPTOR] L%d -> identified root node: %s", level + 1, node_ids_for_level[0]
            )

        try:
            await self.tree_repo.add_nodes(tree_id, node_rows)
            await self.tree_repo.add_edges(tree_id, edge_rows)
            await self.tree_repo.link_node_chunks(link_rows)
            await self.emb_repo.bulk_upsert(emb_rows)
            logger.info(
                "[RAPTOR] L%d persist OK nodes=%d edges=%d links=%d embeds=%d",
                level + 1,
                len(node_rows),
                len(edge_rows),
                len(link_rows),
                len(emb_rows),
            )
        except (IntegrityError, DBAPIError, Exception):
            logger.exception("[RAPTOR] L%d persist FAILED tree_id=%s", level + 1, tree_id)
            raise

        return node_ids_for_level, vecs, summaries

    @staticmethod
    def _aggregate_chunks(member_ids: List[str], node2chunk_ids: Dict[str, List[str]]) -> List[str]:
        seen, agg = set(), []
        for mid in member_ids:
            for cid in node2chunk_ids[mid]:
                if cid not in seen:
                    seen.add(cid)
                    agg.append(cid)
        return agg

    def _ensure_last_ts(self, min_interval: float):
        if not hasattr(self, "_last_embed_ts"):
            self._last_embed_ts = time.perf_counter() - min_interval
