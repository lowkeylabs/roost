# src/owlroost/metrics/aggregation/aggregate_metrics.py

from __future__ import annotations

# =========================================================
# Default Aggregate Formatting
# =========================================================

from .registry import (
    AGG_DEFAULT_FMT,
)

# =========================================================
# Aggregate Definition Normalization
# =========================================================


def normalize_aggregate_definition(
    aggregate,
):
    """
    Normalize aggregate specification.

    Supports:

        "median"

    or:

        ("median", "currency")

    Returns
    -------
    (agg_name, fmt)
    """

    if isinstance(
        aggregate,
        tuple,
    ):
        return aggregate

    return (
        aggregate,
        AGG_DEFAULT_FMT.get(
            aggregate
        ),
    )


# =========================================================
# Aggregate Field Naming
# =========================================================


def build_aggregate_field_name(
    field_name: str,
    agg_name: str,
):
    """
    Construct canonical aggregate
    projection field name.

    Example
    -------
        timing.elapsed_seconds
            +
        median

        ->
        timing.elapsed_seconds__median
    """

    return (
        f"{field_name}"
        f"__{agg_name}"
    )


# =========================================================
# Aggregate Projection Enumeration
# =========================================================


def iter_aggregate_projections(
    metrics_registry,
):
    """
    Yield aggregate projection definitions.

    Notes
    -----
    This subsystem intentionally owns ONLY:

        - aggregate ontology
        - aggregate naming
        - aggregate projection semantics

    It intentionally does NOT own:

        - display overlays
        - rendering
        - formatting
        - presentation metadata

    Display-layer overlay synthesis belongs
    downstream in the display subsystem.
    """

    for metric in metrics_registry.all():

        # =================================================
        # Skip metrics without aggregate definitions
        # =================================================

        if not metric.default_aggregates:
            continue

        # =================================================
        # Aggregate Definitions
        # =================================================

        for aggregate in (
            metric.default_aggregates
        ):

            (
                agg_name,
                agg_fmt,
            ) = normalize_aggregate_definition(
                aggregate
            )

            agg_field_name = (
                build_aggregate_field_name(
                    metric.name,
                    agg_name,
                )
            )

            yield {
                "field_name": (
                    agg_field_name
                ),
                "source_metric": (
                    metric.name
                ),
                "aggregation": (
                    agg_name
                ),
                "fmt": agg_fmt,
                "path": (
                    f"_metrics."
                    f"{agg_field_name}"
                ),
            }
    