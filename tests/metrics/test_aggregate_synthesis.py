from __future__ import annotations

from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)


# =========================================================
# Aggregate Metrics
# =========================================================


def test_aggregate_metric_projection_kind():

    reg = build_metrics_registry()

    m = reg.get(
        "timing.elapsed_seconds__median"
    )

    assert (
        m.projection_kind
        == "aggregate"
    )


def test_aggregate_metric_lineage():

    reg = build_metrics_registry()

    m = reg.get(
        "timing.elapsed_seconds__median"
    )

    assert (
        m.derived_from
        == [
            "timing.elapsed_seconds"
        ]
    )


def test_aggregate_metric_function():

    reg = build_metrics_registry()

    m = reg.get(
        "timing.elapsed_seconds__median"
    )

    assert (
        m.aggregate_function
        == "median"
    )


def test_aggregate_metrics_not_aggregatable():

    reg = build_metrics_registry()

    m = reg.get(
        "timing.elapsed_seconds__median"
    )

    assert (
        m.aggregatable
        is False
    )


def test_aggregate_metrics_materialize_at_run_level():

    reg = build_metrics_registry()

    m = reg.get(
        "timing.elapsed_seconds__median"
    )

    assert (
        m.materialization_level
        == "run"
    )
