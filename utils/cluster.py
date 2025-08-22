import numpy as np
from sklearn.mixture import GaussianMixture
import umap


def umap_reduce(
    X: np.ndarray,
    dim: int,
    metric: str = "cosine",
    n_neighbors: int | None = None,
    local: bool = False,
) -> np.ndarray:
    n = len(X)
    if n <= 2:
        return X.astype(np.float32)

    n_components = max(1, min(dim, n - 2))
    if local:
        n_neighbors = min(n_neighbors or 10, n - 1)
    else:
        n_neighbors = int((n - 1) ** 0.5) or 2

    return umap.UMAP(
        n_neighbors=n_neighbors,
        n_components=n_components,
        metric=metric,
    ).fit_transform(X)


def choose_k_by_bic(X: np.ndarray, min_k: int, max_k: int, random_state: int = 224) -> int:
    ub = max(1, min(max_k, len(X)))
    lb = max(1, min(min_k, ub))
    if lb >= ub:
        return 1
    ks = np.arange(lb, ub + 1)
    bics = []
    for k in ks:
        gm = GaussianMixture(n_components=k, random_state=random_state)
        gm.fit(X)
        bics.append(gm.bic(X))
    return int(ks[int(np.argmin(bics))])


def gmm_soft_clusters(
    X: np.ndarray, threshold: float, max_k: int, random_state: int = 224
) -> tuple[list[list[int]], int]:
    n_clusters = choose_k_by_bic(X, 1, min(max_k, len(X)), random_state)
    gm = GaussianMixture(n_components=n_clusters, random_state=random_state)
    gm.fit(X)
    probs = gm.predict_proba(X)
    labels_per_point = [np.where(p > threshold)[0].tolist() for p in probs]
    return labels_per_point, n_clusters
