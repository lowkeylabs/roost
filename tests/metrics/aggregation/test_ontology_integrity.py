from __future__ import annotations

from owlroost.metrics.aggregation.aggregate_metrics import (
    build_aggregate_field_name,
    iter_aggregate_projections,
)


def test_aggregate_metrics_use_canonical_projection(
    metrics_registry,
):
    """
    Canonical metrics should retain canonical
    semantic identity.

    Aggregate projections are layered
    analytically on top of canonical
    ontology.
    """

    metric = metrics_registry.get(
        "timing.elapsed_seconds"
    )

    assert (
        metric.projection_kind
        == "canonical"
    )


def test_iter_aggregate_projections(
    metrics_registry,
):
    """
    Aggregation subsystem should expose
    aggregate projection ontology.
    """

    projections = list(
        iter_aggregate_projections(
            metrics_registry
        )
    )

    assert projections

    projection = next(
        p
        for p in projections
        if (
            p["field_name"]
            == "timing.elapsed_seconds__median"
        )
    )

    assert (
        projection["source_metric"]
        == "timing.elapsed_seconds"
    )

    assert (
        projection["aggregation"]
        == "median"
    )

    assert (
        projection["path"]
        == "_metrics.timing.elapsed_seconds__median"
    )


def test_aggregate_projection_field_names(
    metrics_registry,
):
    """
    Aggregate projections should follow
    canonical naming conventions.
    """

    projections = list(
        iter_aggregate_projections(
            metrics_registry
        )
    )

    for projection in projections:

        field_name = projection[
            "field_name"
        ]

        assert "__" in field_name


def test_build_aggregate_field_name():
    """
    Aggregate field names should be stable
    and deterministic.
    """

    field_name = (
        build_aggregate_field_name(
            "timing.elapsed_seconds",
            "median",
        )
    )

    assert (
        field_name
        == "timing.elapsed_seconds__median"
    )


def test_trial_metrics_are_aggregated(
    metrics_registry,
):
    """
    Trial-level metrics should support
    analytical aggregation.
    """

    metric = metrics_registry.get(
        "timing.elapsed_seconds"
    )

    assert (
        metric.materialization_level
        == "trial"
    )

    assert (
        metric.default_aggregates
    )
