from __future__ import annotations

from typing import Any, Callable, Dict, List

import numpy as np
from sklearn.mixture import GaussianMixture
import umap


def _reduce(
    embeds: np.ndarray,
    n_neighbors: int = 15,
    n_components: int = 8,
    metric: str = "cosine",
) -> np.ndarray:
    reducer = umap.UMAP(
        n_neighbors=max(2, n_neighbors),
        n_components=min(n_components, max(2, embeds.shape[0] - 1)),
        metric=metric,
    )
    return reducer.fit_transform(embeds)


def _select_k_bic(
    z: np.ndarray,
    k_max: int,
    random_state: int = 42,
) -> int:
    ks = range(1, max(2, min(k_max, len(z))))
    bics: List[float] = []
    for k in ks:
        gm = GaussianMixture(n_components=k, random_state=random_state)
        gm.fit(z)
        bics.append(gm.bic(z))
    return list(ks)[int(np.argmin(bics))]


def build_tree(
    chunks: List[Dict[str, Any]],
    params: Dict[str, Any],
    summarize_fn: Callable[[List[str], int], str],
    embed_fn: Callable[[str], List[float]],
    random_state: int = 42,
) -> List[Dict[str, Any]]:
    """
    chunks: list[dict{text, embedding}]
    summarize_fn(texts:list[str], max_tokens:int) -> str
    embed_fn(text:str) -> list[float]
    """
    nodes: List[Dict[str, Any]] = list(chunks)  # leaf nodes
    layers: List[tuple[int, int]] = [(0, len(nodes))]
    start, end = 0, len(nodes)

    while end - start > 1:
        embeds = np.array([n["embedding"] for n in nodes[start:end]], dtype=np.float32)
        if embeds.shape[0] == 2:
            summary = summarize_fn(
                [nodes[start]["text"], nodes[start + 1]["text"]],
                params["summary"]["max_tokens"],
            )
            nodes.append({"text": summary, "embedding": embed_fn(summary), "is_summary": True})
            layers.append((end, len(nodes)))
            start, end = end, len(nodes)
            continue

        z = _reduce(embeds, **params["umap"])
        k = _select_k_bic(z, params.get("max_cluster", 8), random_state)
        gm = GaussianMixture(n_components=k, random_state=random_state).fit(z)
        labels = gm.predict(z)

        for c in range(k):
            idx = [i for i, lab in enumerate(labels) if lab == c]
            texts = [nodes[start + i]["text"] for i in idx]
            summary = summarize_fn(texts, params["summary"]["max_tokens"])
            nodes.append({"text": summary, "embedding": embed_fn(summary), "is_summary": True})

        layers.append((end, len(nodes)))
        start, end = end, len(nodes)

    # TODO: persist nodes/edges + index vectors
    return nodes
