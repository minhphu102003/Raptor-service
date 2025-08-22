import numpy as np
from sklearn.mixture import GaussianMixture


def choose_k_by_bic(X: np.ndarray, min_k: int, max_k: int, random_state: int) -> int:
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


def gmm_soft_clusters(X: np.ndarray, threshold: float, max_k: int, random_state: int):
    n_clusters = choose_k_by_bic(X, 1, min(max_k, len(X)), random_state)
    gm = GaussianMixture(n_components=n_clusters, random_state=random_state)
    gm.fit(X)
    probs = gm.predict_proba(X)
    labels_per_point = [np.where(p > threshold)[0].tolist() for p in probs]
    return labels_per_point, n_clusters
