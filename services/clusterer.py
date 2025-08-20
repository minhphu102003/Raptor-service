from __future__ import annotations

from typing import List, Optional

import numpy as np
from sklearn.mixture import GaussianMixture
import umap


class GMMRaptorClusterer:
    """
    - UMAP giảm chiều (global, local)
    - Chọn k bằng BIC (GMM)
    - Soft assignment với ngưỡng xác suất (threshold)
    - Trả về list các cụm: List[List[int]] (chỉ số của vector)
    """

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
        # sqrt(n-1)
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

    # ---------- main ----------
    def fit_predict(
        self,
        vectors: List[List[float]],
        *,
        min_k: int = 2,
        max_k: int = 50,
        verbose: bool = False,
    ) -> List[List[int]]:
        """
        Trả về các cụm theo index gốc của 'vectors'.
        Lưu ý: soft assignment → 1 điểm có thể xuất hiện ở nhiều cụm.
        """
        X = np.asarray(vectors, dtype=np.float32)
        n = X.shape[0]
        if n == 0:
            return []
        if n <= min_k:
            return [list(range(n))]

        Xg = self._umap_global(X, self.reduction_dim)
        global_labels_per_point, n_global = self._gmm_soft_clusters(Xg, self.threshold, max_k)
        if verbose:
            print(f"[RAPTOR] Global clusters: {n_global}")

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
            if verbose:
                print(f"[RAPTOR] Global group {gi}: {len(member_idx)} pts")

            if len(member_idx) <= self.reduction_dim + 1:
                for idx in member_idx:
                    all_local_cluster_ids_per_point[idx].append(total_local_clusters)
                total_local_clusters += 1
                continue

            Xl = self._umap_local(X_local, self.reduction_dim)
            labels_per_point_local, n_local = self._gmm_soft_clusters(Xl, self.threshold)
            if verbose:
                print(f"[RAPTOR] Local clusters in global {gi}: {n_local}")

            for offset, local_labels in enumerate(labels_per_point_local):
                orig_idx = member_idx[offset]
                for lab in local_labels:
                    all_local_cluster_ids_per_point[orig_idx].append(total_local_clusters + lab)
            total_local_clusters += n_local

        if total_local_clusters == 0:
            return [list(range(n))]

        groups: list[list[int]] = [[] for _ in range(total_local_clusters)]
        for i, labs in enumerate(all_local_cluster_ids_per_point):
            for lab in labs:
                groups[lab].append(i)

        return [g for g in groups if g]
