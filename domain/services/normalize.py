import math
from typing import List, Sequence


def l2_normalize(vec: Sequence[float]) -> List[float]:
    s = math.sqrt(sum(x * x for x in vec))
    if s == 0.0 or math.isnan(s) or math.isinf(s):
        raise ValueError("Cannot normalize zero/NaN/Inf vector")
    return [x / s for x in vec]


def maybe_normalize(
    vectors: Sequence[Sequence[float]], space: str, normalized: bool
) -> List[List[float]]:
    if space.lower() == "cosine" and normalized:
        return [l2_normalize(v) for v in vectors]
    return [list(v) for v in vectors]
