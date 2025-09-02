from __future__ import annotations

import logging
from typing import List

import numpy as np

from utils.cluster import gmm_soft_clusters, umap_reduce

logger = logging.getLogger("cluster")


class GMMRaptorClusterer:
    def __init__(
        self,
        *,
        metric: str = "cosine",
        reduction_dim: int = 10,
        threshold: float = 0.1,
        random_state: int = 224,
    ):
        self.metric = metric
        self.reduction_dim = reduction_dim
        self.threshold = threshold
        self.random_state = random_state

    def fit_predict(
        self,
        vectors: List[List[float]],
        *,
        min_k: int = 2,
        max_k: int = 50,
        verbose: bool = False,
    ) -> List[List[int]]:
        loglvl = logging.DEBUG if verbose else logging.INFO

        X = np.asarray(vectors, dtype=np.float32)
        n = X.shape[0]
        logger.log(loglvl, "[CLUSTER] Start fit_predict: n=%d, min_k=%d, max_k=%d", n, min_k, max_k)

        if n == 0:
            logger.log(loglvl, "[CLUSTER] Empty input -> []")
            return []
        if n <= min_k:
            logger.log(loglvl, "[CLUSTER] n<=min_k -> single cluster with %d points", n)
            return [list(range(n))]

        if n <= min_k or n <= 3:
            logger.log(loglvl, "[CLUSTER] small n fallback -> single cluster with %d points", n)
            return [list(range(n))]

        Xg = umap_reduce(X, self.reduction_dim, self.metric, local=False)
        global_labels_per_point, n_global = gmm_soft_clusters(Xg, self.threshold, max_k)
        logger.log(loglvl, "[CLUSTER] Global clusters: %d", n_global)

        global_groups: list[list[int]] = [[] for _ in range(n_global)]
        for idx, labs in enumerate(global_labels_per_point):
            for g in labs:
                global_groups[g].append(idx)

        all_local_cluster_ids_per_point: list[list[int]] = [[] for _ in range(n)]
        total_local_clusters = 0

        for gi, member_idx in enumerate(global_groups):
            if not member_idx:
                continue
            X_local = X[np.array(member_idx)]
            logger.log(loglvl, "[CLUSTER] Global group %d: %d pts", gi, len(member_idx))

            if len(member_idx) <= self.reduction_dim + 1:
                for idx in member_idx:
                    all_local_cluster_ids_per_point[idx].append(total_local_clusters)
                total_local_clusters += 1
                logger.log(
                    loglvl,
                    "[CLUSTER] Global group %d -> kept as one local cluster (size=%d)",
                    gi,
                    len(member_idx),
                )
                continue

            Xl = umap_reduce(X_local, self.reduction_dim, self.metric, n_neighbors=10, local=True)

            labels_per_point_local, n_local = gmm_soft_clusters(
                Xl, self.threshold, max_k=max_k, random_state=self.random_state
            )
            logger.log(loglvl, "[CLUSTER] Local clusters in global %d: %d", gi, n_local)

            for offset, local_labels in enumerate(labels_per_point_local):
                orig_idx = member_idx[offset]
                for lab in local_labels:
                    all_local_cluster_ids_per_point[orig_idx].append(total_local_clusters + lab)
            total_local_clusters += n_local

        if total_local_clusters == 0:
            logger.log(
                loglvl, "[CLUSTER] No local clusters -> single cluster fallback with %d points", n
            )
            return [list(range(n))]

        groups: list[list[int]] = [[] for _ in range(total_local_clusters)]
        for i, labs in enumerate(all_local_cluster_ids_per_point):
            for lab in labs:
                groups[lab].append(i)

        logger.log(
            loglvl,
            "[CLUSTER] Filtered singleton clusters: %d ",
            len(groups),
        )

        return groups
