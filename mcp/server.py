from __future__ import annotations

from typing import Callable, TypedDict

import numpy as np
from numpy.typing import NDArray
from sklearn.mixture import GaussianMixture
import umap


class UmapParams(TypedDict):
    n_neighbors: int
    n_components: int
    metric: str


class SummaryParams(TypedDict):
    max_tokens: int


class RaptorParams(TypedDict, total=False):
    max_cluster: int
    umap: UmapParams
    summary: SummaryParams


class Node(TypedDict, total=False):
    text: str
    embedding: list[float]
    is_summary: bool


def _reduce(
    embeds: NDArray[np.float32],
    n_neighbors: int = 15,
    n_components: int = 8,
    metric: str = "cosine",
) -> NDArray[np.float32]:
    reducer = umap.UMAP(
        n_neighbors=max(2, n_neighbors),
        n_components=min(n_components, max(2, int(embeds.shape[0]) - 1)),
        metric=metric,
    )
    z = reducer.fit_transform(embeds)
    return z.astype(np.float32, copy=False)


def _select_k_bic(
    z: NDArray[np.float32],
    k_max: int,
    random_state: int = 42,
) -> int:
    ks = range(1, max(2, min(k_max, z.shape[0])))
    bics: list[float] = []
    for k in ks:
        gm = GaussianMixture(n_components=k, random_state=random_state)
        gm.fit(z)
        bics.append(gm.bic(z))
    return list(ks)[int(np.argmin(np.array(bics, dtype=np.float64)))]


def build_tree(
    chunks: list[Node],
    params: RaptorParams,
    summarize_fn: Callable[[list[str], int], str],
    embed_fn: Callable[[str], list[float]],
    random_state: int = 42,
) -> list[Node]:
    nodes: list[Node] = list(chunks)  # leaf nodes
    layers: list[tuple[int, int]] = [(0, len(nodes))]
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

        umap_cfg: UmapParams = params.get(
            "umap",
            {"n_neighbors": 15, "n_components": 8, "metric": "cosine"},  # type: ignore[typeddict-item]
        )  # mypy: nếu muốn chặt chẽ, hãy đảm bảo trường này luôn có mặt
        z = _reduce(embeds, **umap_cfg)
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

    return nodes
