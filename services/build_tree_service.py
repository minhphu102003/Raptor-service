import asyncio
import logging
import time
from typing import Any, Dict, List
import uuid

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
        tree_id = await self.tree_repo.create_tree(
            doc_id=doc_id, dataset_id=dataset_id, params=params
        )
        logger.info(
            "[RAPTOR] create_tree tree_id=%s doc_id=%s dataset_id=%s", tree_id, doc_id, dataset_id
        )

        current_ids = [it["id"] for it in chunk_items]
        current_vecs = list(vectors)
        level = 0

        id2text = {it["id"]: it["text"] for it in chunk_items}

        llm_conc = int(params.get("llm_concurrency", 3))
        sem = asyncio.Semaphore(max(1, llm_conc))

        async def _summarize(texts: List[str], max_tokens: int) -> str:
            async with sem:
                return await self.summarizer.summarize_cluster(texts, max_tokens=max_tokens)

        while len(current_ids) > 1:
            t0 = time.perf_counter()
            groups = self.clusterer.fit_predict(
                current_vecs,
                min_k=int(params.get("min_k", 2)),
                max_k=int(params.get("max_k", 50)),
                verbose=True,
            )
            sizes = [len(ix) for ix in groups]
            info = getattr(self.clusterer, "last_info", {})
            logger.info(
                "[RAPTOR] L%d clusters=%d sizes=%s score=%s method=%s",
                level + 1,
                len(groups),
                sizes,
                info.get("best_score"),
                info.get("criterion") or "BIC",
            )

            node_rows, edge_rows, link_rows = [], [], []
            new_ids, new_vecs = [], []

            tasks = []
            group_pack = []
            for gi, idxs in enumerate(groups):
                member_ids = [current_ids[i] for i in idxs]
                member_texts = [id2text[mid] for mid in member_ids]
                logger.debug(
                    "[RAPTOR] L%d G%d members=%d ids=%s", level + 1, gi, len(member_ids), member_ids
                )
                group_pack.append((gi, member_ids, member_texts))
                tasks.append(_summarize(member_texts, int(params.get("max_tokens", 256))))

            summaries_for_level = await asyncio.gather(*tasks)

            node_ids_for_level = []
            for (gi, member_ids, member_texts), summary in zip(group_pack, summaries_for_level):
                node_id = f"{tree_id}::L{level + 1}::{gi}::{uuid.uuid4().hex[:6]}"
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
                for mid in member_ids:
                    edge_rows.append({"parent_id": node_id, "child_id": mid})
                for rank, mid in enumerate(member_ids):
                    link_rows.append({"node_id": node_id, "chunk_id": mid, "rank": rank})
                node_ids_for_level.append(node_id)

            rpm_limit = int(params.get("rpm_limit", 3))  #
            min_interval = 60.0 / max(1, rpm_limit)
            now = time.perf_counter()
            sleep_for = (self._last_embed_ts + min_interval) - now
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)

            t_embed = time.perf_counter()
            vecs = await self.embedder.embed_docs(summaries_for_level)
            self._last_embed_ts = time.perf_counter()
            logger.info(
                "[RAPTOR] L%d batch-embed n=%d ms=%.1f",
                level + 1,
                len(summaries_for_level),
                (time.perf_counter() - t_embed) * 1e3,
            )

            emb_rows = []
            for node_id, vec in zip(node_ids_for_level, vecs):
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
                new_ids.append(node_id)
                new_vecs.append(vec)

            await self.tree_repo.add_nodes(tree_id, node_rows)
            await self.tree_repo.add_edges(tree_id, edge_rows)
            await self.tree_repo.link_node_chunks(link_rows)
            await self.emb_repo.bulk_upsert(emb_rows)
            logger.info(
                "[RAPTOR] L%d commit nodes=%d edges=%d ms=%.1f",
                level + 1,
                len(node_rows),
                len(edge_rows),
                (time.perf_counter() - t0) * 1e3,
            )

            current_ids, current_vecs = new_ids, new_vecs
            level += 1

        logger.info("[RAPTOR] done tree_id=%s levels=%d", tree_id, level)
        return tree_id
