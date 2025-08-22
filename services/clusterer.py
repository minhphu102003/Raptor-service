from __future__ import annotations

import logging
from typing import List

import numpy as np
from sklearn.mixture import GaussianMixture
import umap

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

    def _umap_global(self, X: np.ndarray, dim: int) -> np.ndarray:
        n = len(X)
        if n <= 2:
            return X.astype(np.float32)
        n_neighbors = int((n - 1) ** 0.5) or 2
        n_components = max(1, min(dim, n - 2))
        return umap.UMAP(
            n_neighbors=n_neighbors, n_components=n_components, metric=self.metric
        ).fit_transform(X)

    def _umap_local(self, X: np.ndarray, dim: int, num_neighbors: int = 10) -> np.ndarray:
        n = len(X)
        if n <= 2:
            return X.astype(np.float32)
        n_components = max(1, min(dim, n - 2))
        return umap.UMAP(
            n_neighbors=min(num_neighbors, n - 1),
            n_components=n_components,
            metric=self.metric,
        ).fit_transform(X)

    def _choose_k_by_bic(self, X: np.ndarray, min_k: int, max_k: int) -> int:
        ub = max(1, min(max_k, len(X)))
        lb = max(1, min(min_k, ub))
        if lb >= ub:
            return 1
        ks = np.arange(lb, ub + 1)
        bics = []
        for k in ks:
            gm = GaussianMixture(n_components=k, random_state=self.random_state)
            gm.fit(X)
            bics.append(gm.bic(X))
        return int(ks[int(np.argmin(bics))])

    def _gmm_soft_clusters(
        self, X: np.ndarray, threshold: float, max_k: int
    ) -> tuple[list[list[int]], int]:
        n_clusters = self._choose_k_by_bic(X, 1, min(max_k, len(X)))
        gm = GaussianMixture(n_components=n_clusters, random_state=self.random_state)
        gm.fit(X)
        probs = gm.predict_proba(X)
        labels_per_point = [np.where(p > threshold)[0].tolist() for p in probs]
        return labels_per_point, n_clusters

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

        Xg = self._umap_global(X, self.reduction_dim)
        global_labels_per_point, n_global = self._gmm_soft_clusters(Xg, self.threshold, max_k)
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

            Xl = self._umap_local(X_local, self.reduction_dim)
            labels_per_point_local, n_local = self._gmm_soft_clusters(
                Xl, self.threshold, max_k=max_k
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
