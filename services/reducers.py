import numpy as np
import umap


def umap_global(X: np.ndarray, dim: int, metric: str) -> np.ndarray:
    X = np.asarray(X, dtype=np.float32)
    n = len(X)
    if n <= 2:
        return X
    base = int((n - 1) ** 0.5)
    n_neighbors = max(2, min(n - 1, base))
    n_components = max(1, min(dim, n - 1))

    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        n_components=n_components,
        metric=metric,
    )
    return reducer.fit_transform(X)


def umap_local(X: np.ndarray, dim: int, metric: str, num_neighbors: int = 10) -> np.ndarray:
    n = len(X)
    if n <= 2:
        return X.astype(np.float32)
    n_components = max(1, min(dim, n - 2))
    return umap.UMAP(
        n_neighbors=min(num_neighbors, n - 1),
        n_components=n_components,
        metric=metric,
    ).fit_transform(X)
