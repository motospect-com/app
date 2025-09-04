# Minimal stub of NumPy for offline MotoSpect tests
# Provides only the functions used by the codebase.

from __future__ import annotations

import random as _random
import math as _math
import builtins
from typing import List, Sequence, Tuple

__all__ = [
    "array",
    "arange",
    "mean",
    "var",
    "min",
    "max",
    "polyfit",
    "random",
]

# ---------------------------------------------------------------------------
# Basic helpers (1-D only)
# ---------------------------------------------------------------------------

def array(seq: Sequence, dtype=float):
    """Return list of dtype-cast elements (very lightweight)."""
    return [dtype(item) for item in seq]


def arange(n: int):
    """Return list [0, 1, ..., n-1]."""
    return list(range(n))


def mean(values: Sequence[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else float("nan")


def var(values: Sequence[float]) -> float:
    m = mean(values)
    return sum((v - m) ** 2 for v in values) / len(values) if values else float("nan")


def min(values: Sequence[float]):
    return builtins.min(values)


def max(values: Sequence[float]):
    return builtins.max(values)

# ---------------------------------------------------------------------------
# Very small linear regression implementation for polyfit (deg==1 only)
# ---------------------------------------------------------------------------

def _linear_regression(x: List[float], y: List[float]) -> Tuple[float, float]:
    n = len(x)
    if n == 0:
        return 0.0, 0.0
    sum_x = sum(x)
    sum_y = sum(y)
    sum_x2 = sum(v * v for v in x)
    sum_xy = sum(vx * vy for vx, vy in zip(x, y))
    denom = n * sum_x2 - sum_x ** 2
    if denom == 0:
        return 0.0, 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def polyfit(x: Sequence[float], y: Sequence[float], deg: int):
    if deg != 1:
        raise NotImplementedError("stub polyfit supports only deg=1")
    return _linear_regression(list(x), list(y))

# ---------------------------------------------------------------------------
# Random sub-module stub
# ---------------------------------------------------------------------------

class _RandomModule:
    def rand(self, n: int):  # type: ignore
        """Return list of n uniform random floats in range [0,1)."""
        return [_random.random() for _ in range(n)]


random = _RandomModule()
