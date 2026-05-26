# src/owlroost/metrics/aggregation/service.py

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

    Returns:
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

    if agg_name in (
        "cnt",
        "cnt_true",
    ):
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

    Returns flat aggregate dict:

        financial.bequest.total__median
        elapsed_seconds__p90
        etc.
    """

    out = {}

    if not rows:
        return out

    # =====================================================
    # Iterate Metrics
    # =====================================================

    for metric in metrics_registry.all():
        # -------------------------------------------------
        # Only aggregate trial metrics
        # -------------------------------------------------

        if metric.compute_level != "trial":
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

        # -------------------------------------------------
        # Collect numeric values
        # -------------------------------------------------

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

        for agg_name, fmt in _normalize_aggregates(metric):
            func = get_aggregation_func(agg_name)

            if func is None:
                raise ValueError(f"Unknown aggregation: {agg_name}")

            agg_field_name = build_aggregate_field_name(
                metric.name,
                agg_name,
            )

            # ---------------------------------------------
            # Empty dataset handling
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

    Returns aggregate metric dict.

    Intended primarily for:

        trial -> run

    aggregation.
    """

    return aggregate_rows(
        rows=list(dataset.rows),
        metrics_registry=metrics_registry,
    )
