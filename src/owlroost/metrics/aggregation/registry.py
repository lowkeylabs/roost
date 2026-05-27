# src/owlroost/metrics/aggregation/registry.py

from __future__ import annotations

import statistics
from collections.abc import (
    Callable,
)
from typing import (
    Any,
)

import numpy as np

from .context import (
    AggregationExplainFn,
)

# =========================================================
# Aggregation Function Typing
# =========================================================

AggregationFunc = Callable[
    [list[Any]],
    Any,
]

# =========================================================
# Default Aggregate Display Formats
# =========================================================

AGG_DEFAULT_FMT: dict[
    str,
    str | None,
] = {
    "cnt": "int",
    "cnt_true": "int",
    "pct": "percent",
    "ratio": "count_ratio",
    "mean": "float2",
    "median": "float2",
    "sum": "float2",
    "std": "float2",
    "min": "float2",
    "max": "float2",
    "p10": "float2",
    "p90": "float2",
    "p99": "float2",
}

# =========================================================
# Canonical Aggregation Registry
# =========================================================

AGG_FUNCS: dict[
    str,
    AggregationFunc,
] = {}

# =========================================================
# Explainability Registry
# =========================================================

AGG_EXPLAINS: dict[
    str,
    AggregationExplainFn,
] = {}

# =========================================================
# Registration
# =========================================================


def register_aggregation(
    name: str,
    func: AggregationFunc,
    explain: (
        AggregationExplainFn | None
    ) = None,
):
    """
    Register canonical aggregation function.

    Notes
    -----
    Aggregation names form part of ROOST's
    analytical ontology.

    Example
    -------
        timing.elapsed_seconds
            +
        median

        ->
        timing.elapsed_seconds__median

    Therefore duplicate registrations are
    considered ontology errors.
    """

    if name in AGG_FUNCS:
        raise ValueError(
            "Aggregation already "
            f"registered: {name}"
        )

    AGG_FUNCS[name] = func

    if explain is not None:
        AGG_EXPLAINS[name] = explain


# =========================================================
# Lookup Helpers
# =========================================================


def get_aggregation_func(
    name: str,
):
    """
    Retrieve aggregation implementation.
    """

    return AGG_FUNCS.get(name)


def get_aggregation_explain(
    name: str,
):
    """
    Retrieve aggregation explainability
    helper.
    """

    return AGG_EXPLAINS.get(name)


def list_aggregations():
    """
    Return stable sorted aggregation names.
    """

    return sorted(
        AGG_FUNCS.keys()
    )


# =========================================================
# Built-In Aggregations
# =========================================================


register_aggregation(
    "mean",
    statistics.mean,
)

register_aggregation(
    "median",
    statistics.median,
)

register_aggregation(
    "sum",
    sum,
)

register_aggregation(
    "min",
    min,
)

register_aggregation(
    "max",
    max,
)

register_aggregation(
    "std",
    lambda v: (
        statistics.stdev(v)
        if len(v) >= 2
        else 0.0
    ),
)

register_aggregation(
    "p10",
    lambda v: float(
        np.percentile(v, 10)
    ),
)

register_aggregation(
    "p90",
    lambda v: float(
        np.percentile(v, 90)
    ),
)

register_aggregation(
    "p99",
    lambda v: float(
        np.percentile(v, 99)
    ),
)

register_aggregation(
    "cnt",
    lambda v: len(v),
)

register_aggregation(
    "cnt_true",
    lambda v: sum(
        bool(x) for x in v
    ),
)

register_aggregation(
    "pct",
    lambda v: (
        (
            sum(bool(x) for x in v)
            / len(v)
        )
        if v
        else 0.0
    ),
)

# =========================================================
# Optional Ratio Aggregation
# =========================================================


register_aggregation(
    "ratio",
    lambda v: (
        (
            sum(bool(x) for x in v)
            / len(v)
        )
        if v
        else 0.0
    ),
)
