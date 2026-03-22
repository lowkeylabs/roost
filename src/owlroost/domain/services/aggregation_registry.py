import math
import statistics
from collections.abc import Callable
from typing import Any

# =========================================================
# Core aggregation functions
# =========================================================


def mean(values):
    return statistics.mean(values) if values else None


def median(values):
    return statistics.median(values) if values else None


def sum_(values):
    return sum(values) if values else 0


def min_(values):
    return min(values) if values else None


def max_(values):
    return max(values) if values else None


def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * (p / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    return values[f] + (values[c] - values[f]) * (k - f)


def len_(values):
    return len(values) if values else 0


# =========================================================
# Registry
# =========================================================

AGG_FUNCS: dict[str, Callable[[list[Any]], Any]] = {}
AGG_EXPLAINS: dict[str, Callable[[list[Any]], str]] = {}


def register_aggregation(
    name: str,
    func: Callable[[list[Any]], Any],
    explain: Callable[[list[Any]], str] | None = None,
):
    AGG_FUNCS[name] = func

    if explain:
        AGG_EXPLAINS[name] = explain


def get_aggregation_func(name: str):
    return AGG_FUNCS.get(name)


def get_aggregation_explain(name: str):
    return AGG_EXPLAINS.get(name)


# =========================================================
# Default registrations
# =========================================================

register_aggregation(
    "mean",
    mean,
    explain=lambda v: f"average across rows (n={len(v)})",
)

register_aggregation(
    "pct",
    mean,
    explain=lambda v: f"average (percent-style metric) (n={len(v)})",
)

register_aggregation(
    "cnt",
    len_,
    explain=lambda v: f"count of rows (n={len(v)})",
)

register_aggregation(
    "median",
    median,
    explain=lambda v: f"median (50th percentile) (n={len(v)})",
)

register_aggregation(
    "sum",
    sum_,
    explain=lambda v: f"sum across rows (n={len(v)})",
)

register_aggregation(
    "min",
    min_,
    explain=lambda v: f"minimum value across rows (n={len(v)})",
)

register_aggregation(
    "max",
    max_,
    explain=lambda v: f"maximum value across rows (n={len(v)})",
)

register_aggregation(
    "p10",
    lambda v: percentile(v, 10),
    explain=lambda v: f"10th percentile (downside outcome) (n={len(v)})",
)

register_aggregation(
    "p90",
    lambda v: percentile(v, 90),
    explain=lambda v: f"90th percentile (upside outcome) (n={len(v)})",
)
