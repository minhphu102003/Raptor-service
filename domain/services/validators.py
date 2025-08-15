from typing import Sequence


def ensure_dim(vectors: Sequence[Sequence[float]], dim: int):
    for i, v in enumerate(vectors):
        if len(v) != dim:
            raise ValueError(f"DIM_MISMATCH at index {i}: got {len(v)}, expect {dim}")


def ensure_finite(vectors: Sequence[Sequence[float]]):
    import math

    for i, v in enumerate(vectors):
        for x in v:
            if math.isnan(x) or math.isinf(x):
                raise ValueError(f"NaN/Inf at vector {i}")
