from __future__ import annotations

from owlroost.metrics.plugins.owl_outputs import (
    CANONICAL_METRICS,
)

# =========================================================
# Canonical Metrics
# =========================================================


def test_canonical_metrics_have_unique_names():
    names = [metric.name for metric in CANONICAL_METRICS]

    assert len(names) == len(set(names))


def test_canonical_metrics_projection_kinds():
    for metric in CANONICAL_METRICS:
        assert metric.projection_kind in {
            "canonical",
            "synthetic",
        }


def test_canonical_metrics_have_no_aggregate_suffix():
    for metric in CANONICAL_METRICS:
        if metric.projection_kind == "canonical":
            assert "__" not in metric.name


def test_canonical_metrics_have_materialization():
    for metric in CANONICAL_METRICS:
        assert metric.materialization_level is not None
