import math
import statistics
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

AGG_DEFAULT_FMT = {
    "cnt": "int",
    "cnt_true": "int",
    "pct": "percent",
    "ratio": "count_ratio",
    "mean": None,
    "median": None,
    "sum": None,
    "min": None,
    "max": None,
    "p10": None,
    "p90": None,
    "p99": None,
}


@dataclass(slots=True)
class AggContext:
    agg_values: list[Any]  # aggregated values (displayed)
    n_valid: int | None  # non-null values used in aggregation
    n_total: int | None  # total rows considered
    aggregation: str | None
    metric_key: str  # e.g. "bequest"


type AggExplainFn = Callable[[AggContext], str]


# =========================================================
# Core aggregation functions
# =========================================================


def mean(values):
    return statistics.mean(values) if values else None


def std(values):
    return statistics.stdev(values) if len(values) > 1 else 0


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


def cnt_true(values):
    return sum(values) if values else 0


def ratio(values):
    if not values:
        return (0, 0)
    return (sum(values), len(values))


# =========================================================
# Registry
# =========================================================

AGG_FUNCS: dict[str, Callable[[list[Any]], Any]] = {}
AGG_EXPLAINS: dict[str, AggExplainFn] = {}


def register_aggregation(
    name: str,
    func: Callable[[list[Any]], Any],
    explain: AggExplainFn | None = None,
):
    AGG_FUNCS[name] = func

    if explain:
        AGG_EXPLAINS[name] = explain


def get_aggregation_func(name: str):
    return AGG_FUNCS.get(name)


def get_aggregation_explain(name: str):
    return AGG_EXPLAINS.get(name)


# =========================================================
# Default registrations (REVISED)
# =========================================================

register_aggregation(
    "mean",
    mean,
    explain=lambda ctx: (
        "Average" + (f" based on {ctx.n_valid}/{ctx.n_total} observations" if ctx.n_total else "")
    ),
)

register_aggregation(
    "std",
    std,
    explain=lambda ctx: (
        "Standard deviation"
        + (f" based on {ctx.n_valid}/{ctx.n_total} observations" if ctx.n_total else "")
    ),
)

register_aggregation(
    "pct",
    mean,
    explain=lambda ctx: (
        "Based on "
        + (f"{ctx.n_valid}/{ctx.n_total} observations" if ctx.n_total else "available observations")
    ),
)

register_aggregation(
    "cnt",
    len_,
    explain=lambda ctx: (
        f"{ctx.n_valid}/{ctx.n_total} observations"
        if ctx.n_total is not None
        else "Count of observations"
    ),
)

register_aggregation(
    "cnt_true",
    cnt_true,
    explain=lambda ctx: (
        f"{sum(ctx.agg_values)}/{ctx.n_total} true observations"
        if ctx.n_total is not None
        else "Count of true values"
    ),
)

register_aggregation(
    "median",
    median,
    explain=lambda ctx: (
        "Median (50th percentile)"
        + (f" based on {ctx.n_valid}/{ctx.n_total} observations" if ctx.n_total else "")
    ),
)

register_aggregation(
    "sum",
    sum_,
    explain=lambda ctx: (
        "Total" + (f" based on {ctx.n_valid}/{ctx.n_total} observations" if ctx.n_total else "")
    ),
)

register_aggregation(
    "min",
    min_,
    explain=lambda ctx: (
        "Minimum observed value"
        + (f" (based on {ctx.n_valid}/{ctx.n_total} observations)" if ctx.n_total else "")
    ),
)

register_aggregation(
    "max",
    max_,
    explain=lambda ctx: (
        "Maximum observed value"
        + (f" (based on {ctx.n_valid}/{ctx.n_total} observations)" if ctx.n_total else "")
    ),
)

register_aggregation(
    "p10",
    lambda v: percentile(v, 10),
    explain=lambda ctx: (
        "10th percentile (downside outcome)"
        + (f" based on {ctx.n_valid}/{ctx.n_total} observations" if ctx.n_total else "")
    ),
)

register_aggregation(
    "p90",
    lambda v: percentile(v, 90),
    explain=lambda ctx: (
        "90th percentile (upside outcome)"
        + (f" based on {ctx.n_valid}/{ctx.n_total} observations" if ctx.n_total else "")
    ),
)

register_aggregation(
    "p99",
    lambda v: percentile(v, 99),
    explain=lambda ctx: (
        "99th percentile (upside outcome)"
        + (f" based on {ctx.n_valid}/{ctx.n_total} observations" if ctx.n_total else "")
    ),
)


register_aggregation(
    "ratio",
    ratio,
    explain=lambda ctx: (
        f"{sum(ctx.agg_values)}/{ctx.n_total} true observations"
        if ctx.n_total is not None
        else "Ratio of true values"
    ),
)
