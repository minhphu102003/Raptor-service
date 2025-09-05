import asyncio
from collections import deque
from dataclasses import dataclass
import heapq
import logging
import os
import re
import time
from typing import Callable, List, Optional, Tuple

from dotenv import load_dotenv
import voyageai
from voyageai.error import APIConnectionError, APIError, RateLimitError

from utils.log import preview
from utils.packing import count_tokens_total, token_lengths
from utils.ratelimit import RateLimiter

logger = logging.getLogger("voyage")
load_dotenv()


@dataclass
class _ClientSlot:
    key: str
    client: voyageai.AsyncClient  # type: ignore
    limiter: RateLimiter
    sem: asyncio.Semaphore
    # Track when this slot will be available again
    next_available_time: float = 0.0
    # Track if this slot is currently rate-limited
    is_rate_limited: bool = False
    # Track request count for load balancing
    request_count: int = 0


class VoyageEmbeddingClientAsync:
    def __init__(
        self,
        model: str = "voyage-context-3",
        out_dim: int = 1024,
        out_dtype: str = "float",
        rpm_limit: int = 3,
        tpm_limit: int = 10_000,
        max_retries: int = 3,
        per_request_token_budget: int = 9_500,
        *,
        extra_api_keys: Optional[List[str]] = None,
        per_slot_max_concurrent: int = 2,
        log_chunks: bool = False,
        chunk_preview_chars: int = 160,
    ):
        self.model = model
        self.out_dim = out_dim
        self.out_dtype = out_dtype
        self.max_retries = max_retries
        self.per_request_token_budget = per_request_token_budget
        self.log_chunks = log_chunks
        self.chunk_preview_chars = chunk_preview_chars

        self.keys = self._collect_api_keys(extra_api_keys)
        if not self.keys:
            raise RuntimeError("No Voyage API key provided")

        self.slots: List[_ClientSlot] = []
        for k in self.keys:
            cli = voyageai.AsyncClient(api_key=k, max_retries=max_retries)  # type: ignore
            limiter = RateLimiter(rpm=rpm_limit, tpm=tpm_limit)
            sem = asyncio.Semaphore(per_slot_max_concurrent)
            self.slots.append(_ClientSlot(key=k, client=cli, limiter=limiter, sem=sem))

        self._rr = 0
        logger.info("[Voyage] slots=%d", len(self.slots))
        # Queue for requests waiting for available slots
        self.waiting_queue = deque()

    @staticmethod
    def _collect_api_keys(extra_api_keys: Optional[List[str]]) -> List[str]:
        keys: List[str] = []
        base = os.getenv("VOYAGEAI_KEY")
        if base:
            keys.append(base)

        if extra_api_keys:
            keys.extend([k for k in extra_api_keys if k])

        pat = re.compile(r"^VOYAGEAI_KEY_(\d+)$")
        numbered = []
        for name, val in os.environ.items():
            m = pat.match(name)
            if m and val:
                numbered.append((int(m.group(1)), val))
        for _, val in sorted(numbered, key=lambda x: x[0]):
            keys.append(val)

        seen = set()
        uniq = []
        for k in keys:
            if k and k not in seen:
                uniq.append(k)
                seen.add(k)
        return uniq

    def _get_best_available_slot(self) -> Optional[_ClientSlot]:
        """Get the best available slot (least used or not rate-limited)"""
        now = time.time()
        available_slots = []

        for slot in self.slots:
            # Update rate limit status if enough time has passed
            if slot.is_rate_limited and now >= slot.next_available_time:
                slot.is_rate_limited = False
                slot.next_available_time = 0.0

            # Add to available slots if not rate-limited
            if not slot.is_rate_limited:
                available_slots.append(slot)

        if available_slots:
            # Return the slot with the least request count (load balancing)
            return min(available_slots, key=lambda s: s.request_count)

        # If all slots are rate-limited, return None
        return None

    async def _wait_for_best_slot(self) -> _ClientSlot:
        """Wait for the best available slot and return it"""
        while True:
            slot = self._get_best_available_slot()
            if slot:
                return slot

            # All slots are rate-limited, find the one that will be available soonest
            soonest_slot = min(self.slots, key=lambda s: s.next_available_time)
            now = time.time()
            wait_time = max(0, soonest_slot.next_available_time - now)

            if wait_time > 0:
                logger.info(
                    f"[Voyage] All keys rate-limited, waiting {wait_time:.2f}s for key to become available"
                )
                await asyncio.sleep(min(wait_time, 1.0))  # Wait in 1-second increments
            else:
                # Slot should be available now
                soonest_slot.is_rate_limited = False
                soonest_slot.next_available_time = 0.0
                return soonest_slot

    async def _embed_queries_with_failover(self, queries: List[str]) -> List[List[float]]:
        """Embed queries with automatic failover to other keys when rate-limited"""
        if not queries:
            return []

        # Get the best available slot
        slot = await self._wait_for_best_slot()
        slot.request_count += 1

        total_tok = count_tokens_total(queries, model=self.model, api_key=slot.key)
        logger.info("[Voyage] embed_queries n=%d total_tokens=%d", len(queries), total_tok)

        last_err = None
        try:
            await slot.limiter.acquire(total_tok)
        except RateLimitError as e:
            # Mark this slot as rate-limited
            slot.is_rate_limited = True
            slot.next_available_time = time.time() + 60  # Assume 1 minute rate limit window
            slot.request_count -= 1
            # Try with another slot
            slot = await self._wait_for_best_slot()
            slot.request_count += 1
            await slot.limiter.acquire(total_tok)

        for attempt in range(self.max_retries + 1):
            try:
                resp = await slot.client.contextualized_embed(
                    inputs=[[q] for q in queries],
                    model=self.model,
                    input_type="query",
                    output_dimension=self.out_dim,
                    output_dtype=self.out_dtype,
                )
                slot.request_count -= 1
                return [list(r.embeddings[0]) for r in resp.results]
            except RateLimitError as e:
                last_err = e
                # Mark this slot as rate-limited
                slot.is_rate_limited = True
                slot.next_available_time = time.time() + 60  # Assume 1 minute rate limit window
                slot.request_count -= 1

                if attempt < self.max_retries:
                    # Wait for a better slot before retrying
                    logger.info(
                        f"[Voyage] Rate limited, switching to another key (attempt {attempt + 1}/{self.max_retries})"
                    )
                    slot = await self._wait_for_best_slot()
                    slot.request_count += 1
                    continue
                else:
                    # All retries exhausted
                    break
            except (APIConnectionError, APIError) as e:
                last_err = e
                if attempt < self.max_retries:
                    await asyncio.sleep(min(2**attempt, 8))
                else:
                    slot.request_count -= 1
                    break
            except Exception as e:
                slot.request_count -= 1
                raise e

        slot.request_count -= 1
        raise last_err or RuntimeError("unknown embedding error")

    def _pick_slot(self) -> _ClientSlot:
        slot = self.slots[self._rr % len(self.slots)]
        self._rr += 1
        return slot

    async def _embed_one_group(self, gi: int, group: List[str], slot: _ClientSlot):
        group_tokens = count_tokens_total(group, model=self.model, api_key=slot.key)

        async with slot.sem:
            t_wait = time.perf_counter()
            await slot.limiter.acquire(group_tokens)
            waited_ms = (time.perf_counter() - t_wait) * 1e3

            last_err = None
            for attempt in range(self.max_retries + 1):
                t0 = time.perf_counter()
                try:
                    resp = await slot.client.contextualized_embed(
                        inputs=[group],
                        model=self.model,
                        input_type="document",
                        output_dimension=self.out_dim,
                        output_dtype=self.out_dtype,
                    )
                    lat_ms = (time.perf_counter() - t0) * 1e3
                    r0 = resp.results[0]
                    return gi, r0.embeddings, group, waited_ms, lat_ms
                except RateLimitError as e:
                    last_err = e
                    await asyncio.sleep(min(2**attempt, 8))
                except (APIConnectionError, APIError) as e:
                    last_err = e
                    await asyncio.sleep(min(2**attempt, 8))

            raise last_err or RuntimeError("unknown embedding error")

    def _pack_groups_by_tpm(self, chunks: List[str]) -> List[List[str]]:
        lens = token_lengths(chunks, self.model, self.keys[0])
        groups, cur, used = [], [], 0
        for ch, n in zip(chunks, lens):
            if n > self.per_request_token_budget:
                if cur:
                    groups.append(cur)
                    cur, used = [], 0
                groups.append([ch])
                continue
            if used + n > self.per_request_token_budget and cur:
                groups.append(cur)
                cur, used = [], 0
            cur.append(ch)
            used += n
        if cur:
            groups.append(cur)

        sizes = list(map(len, groups))
        tok_each = [count_tokens_total(g, self.model, self.keys[0]) for g in groups]
        logger.info(
            "[Voyage] pack groups: groups=%d sizes=%s tokens=%s (budget=%d)",
            len(groups),
            sizes,
            tok_each,
            self.per_request_token_budget,
        )
        return groups

    async def embed_doc_fulltext_multi(
        self,
        text: str,
        *,
        chunk_fn: Optional[Callable[[str], List[str]]] = None,
    ) -> Tuple[List[List[float]], List[str]]:
        chunks = chunk_fn(text) if chunk_fn else [text]
        groups = self._pack_groups_by_tpm(chunks)

        if len(self.slots) == 1 or len(groups) == 1:
            return await self._embed_doc_fulltext_rate_limited_single(text, chunk_fn=chunk_fn)

        tasks = []
        for gi, group in enumerate(groups):
            slot = self._pick_slot()
            tasks.append(self._embed_one_group(gi, group, slot))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        ordered: List[Tuple[int, List[List[float]], List[str], float, float]] = []
        for r in results:
            if isinstance(r, Exception):
                raise r
            # Type cast to help the type checker understand the type after the isinstance check
            ordered.append(r)  # type: ignore
        ordered.sort(key=lambda x: x[0])

        all_embeddings, all_chunks = [], []
        for _, embs, group, _, _ in ordered:
            all_embeddings.extend(embs)
            all_chunks.extend(group)
        return all_embeddings, all_chunks

    async def _embed_doc_fulltext_rate_limited_single(
        self,
        text: str,
        *,
        chunk_fn: Optional[Callable[[str], List[str]]] = None,
    ) -> Tuple[List[List[float]], List[str]]:
        chunks = chunk_fn(text) if chunk_fn else [text]
        tot_tok = count_tokens_total(chunks, self.model, self.keys[0])
        if self.log_chunks:
            previews = [preview(c, self.chunk_preview_chars) for c in chunks[:20]]
            more = "" if len(chunks) <= 20 else f" (+{len(chunks) - 20} more)"
            logger.info(
                "[Voyage] single chunks n=%d total_tokens=%d previews=%s%s",
                len(chunks),
                tot_tok,
                previews,
                more,
            )
        else:
            logger.info("[Voyage] single chunks n=%d total_tokens=%d", len(chunks), tot_tok)

        slot = self._pick_slot() if hasattr(self, "_pick_slot") else self.slots[0]

        t0 = time.perf_counter()
        async with slot.sem:
            resp = await slot.client.contextualized_embed(
                inputs=[chunks],
                model=self.model,
                input_type="document",
                output_dimension=self.out_dim,
                output_dtype=self.out_dtype,
            )
        lat_ms = (time.perf_counter() - t0) * 1e3

        r0 = resp.results[0]
        logger.info(
            "[Voyage] single done lat_ms=%.1f out_emb=%d dim=%d",
            lat_ms,
            len(r0.embeddings),
            self.out_dim,
        )
        return [list(embed) for embed in r0.embeddings], chunks

    async def embed_queries(self, queries: List[str]) -> List[List[float]]:
        # Use the new failover implementation for better rate limiting handling
        return await self._embed_queries_with_failover(queries)
