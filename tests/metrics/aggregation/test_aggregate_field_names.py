from __future__ import annotations

from owlroost.metrics.aggregation.aggregate_metrics import (
    build_aggregate_field_name,
)


def test_build_aggregate_field_name():
    out = build_aggregate_field_name(
        "timing.elapsed_seconds",
        "median",
    )

    assert out == "timing.elapsed_seconds__median"


def test_aggregate_field_name_contains_suffix():
    out = build_aggregate_field_name(
        "financial.spending.total",
        "p90",
    )

    assert out.endswith("__p90")
