from __future__ import annotations

from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)
from owlroost.metrics.plugins.output_metrics import (
    CANONICAL_METRICS,
)


# =========================================================
# Ontology Layering
# =========================================================


def test_canonical_metrics_do_not_use_aggregate_projection():

    for metric in CANONICAL_METRICS:

        if (
            metric.projection_kind
            == "canonical"
        ):
            assert (
                "__" not in metric.name
            )


def test_aggregate_metrics_use_aggregate_projection():

    reg = build_metrics_registry()

    aggregates = [
        m
        for m in reg.all()
        if "__" in m.name
    ]

    assert aggregates

    for metric in aggregates:

        assert (
            metric.projection_kind
            == "aggregate"
        )


def test_synthetic_metrics_use_synthetic_projection():

    for metric in CANONICAL_METRICS:

        if (
            metric.projection_kind
            == "synthetic"
        ):
            assert (
                metric.projection_kind
                == "synthetic"
            )


def test_metric_names_are_unique_after_bootstrap():

    reg = build_metrics_registry()

    names = [
        m.name
        for m in reg.all()
    ]

    assert len(names) == len(
        set(names)
    )
