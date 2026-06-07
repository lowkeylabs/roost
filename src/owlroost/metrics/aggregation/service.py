# src/owlroost/metrics/aggregation/service.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.metrics.aggregation.aggregate_metrics import (
    build_aggregate_field_name,
)
from owlroost.metrics.aggregation.registry import (
    AGG_DEFAULT_FMT,
    get_aggregation_func,
)

# =========================================================
# Helpers
# =========================================================


def _is_numeric(
    value,
):
    """
    Return whether value participates in
    numeric aggregation semantics.

    Notes
    -----
    Bool intentionally excluded even though
    bool subclasses int.
    """

    return isinstance(
        value,
        int | float,
    ) and not isinstance(
        value,
        bool,
    )


def _normalize_aggregates(
    metric_spec,
):
    """
    Normalize aggregate definitions.

    Supports:

        ["median", "p90"]

    or:

        [("median", "currency")]

    Returns
    -------
    list[(agg_name, fmt)]
    """

    result = []

    for agg in metric_spec.default_aggregates or []:
        if isinstance(
            agg,
            tuple,
        ):
            agg_name, fmt = agg

        else:
            agg_name = agg

            fmt = AGG_DEFAULT_FMT.get(agg_name)

        result.append(
            (
                agg_name,
                fmt,
            )
        )

    return result


def _empty_aggregate_value(
    agg_name: str,
):
    """
    Return canonical empty aggregate value.

    Aggregations over empty datasets should
    never raise runtime exceptions.
    """

    if agg_name in {
        "cnt",
        "cnt_true",
    }:
        return 0

    return None


# =========================================================
# Aggregate Single Metric Row Set
# =========================================================


def aggregate_rows(
    rows: list[dict],
    metrics_registry,
):
    """
    Aggregate trial rows into summary metrics.

    Notes
    -----
    Aggregation semantics are ontology-driven.

    Metrics participate in aggregation only
    when:

        materialization_level == "trial"

    and:

        aggregatable == True

    Returns
    -------
    Flat aggregate metric dict.

    Example
    -------
        timing.elapsed_seconds__median
        financial.bequest.total__p90
    """

    out = {}

    # =====================================================
    # Empty Dataset
    # =====================================================

    if not rows:
        return out

    # =====================================================
    # Iterate Metrics
    # =====================================================

    for metric in metrics_registry.all():
        # -------------------------------------------------
        # Only aggregate trial-materialized metrics
        # -------------------------------------------------

        if metric.materialization_level != "trial":
            continue

        # -------------------------------------------------
        # Skip non-aggregatable metrics
        # -------------------------------------------------

        if not metric.aggregatable:
            continue

        # -------------------------------------------------
        # Skip metrics with no aggregates
        # -------------------------------------------------

        if not metric.default_aggregates:
            continue

        # =================================================
        # Collect Numeric Values
        # =================================================

        values = []

        for row in rows:
            metrics = row.get(
                "_metrics",
                {},
            )

            value = metrics.get(metric.name)

            if _is_numeric(value):
                values.append(value)

        # =================================================
        # Execute Aggregations
        # =================================================

        for (
            agg_name,
            fmt,
        ) in _normalize_aggregates(metric):
            func = get_aggregation_func(agg_name)

            if func is None:
                raise ValueError(f"Unknown aggregation: {agg_name}")

            agg_field_name = build_aggregate_field_name(
                metric.name,
                agg_name,
            )

            # ---------------------------------------------
            # Empty value handling
            # ---------------------------------------------

            if not values:
                out[agg_field_name] = _empty_aggregate_value(agg_name)

                out[f"{agg_field_name}__n_valid"] = 0

                out[f"{agg_field_name}__n_total"] = len(rows)

                if fmt is not None:
                    out[f"{agg_field_name}__fmt"] = fmt

                continue

            # ---------------------------------------------
            # Execute aggregation
            # ---------------------------------------------

            result = func(values)

            out[agg_field_name] = result

            out[f"{agg_field_name}__n_valid"] = len(values)

            out[f"{agg_field_name}__n_total"] = len(rows)

            if fmt is not None:
                out[f"{agg_field_name}__fmt"] = fmt

    return out


# =========================================================
# Aggregate Dataset
# =========================================================


def aggregate_dataset(
    dataset,
    metrics_registry,
):
    """
    Aggregate Dataset rows.

    Intended primarily for:

        trial -> run

    aggregation.
    """

    return aggregate_rows(
        rows=list(dataset.rows),
        metrics_registry=metrics_registry,
    )
