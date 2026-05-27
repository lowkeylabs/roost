from __future__ import annotations

from owlroost.display.registry import (
    DisplayRegistry,
)

from owlroost.metrics.aggregation.aggregate_metrics import (
    register_aggregate_display_fields,
)


def test_aggregate_metrics_use_aggregate_projection(
    metrics_registry,
):

    metric = metrics_registry.get(
        "timing.elapsed_seconds"
    )

    assert (
        metric.projection_kind
        == "canonical"
    )


def test_aggregate_display_fields_do_not_create_new_semantic_identity(
    metrics_registry,
):

    reg = DisplayRegistry()

    register_aggregate_display_fields(
        reg,
        metrics_registry,
    )

    field = reg.get_display_field(
        "timing.elapsed_seconds__median"
    )

    assert (
        field.semantic_field
        is None
        or field.semantic_field
        == metrics_registry.get(
            "timing.elapsed_seconds"
        )
    )


def test_trial_metrics_are_aggregated(
    metrics_registry,
):

    metric = metrics_registry.get(
        "timing.elapsed_seconds"
    )

    assert (
        metric.materialization_level
        == "trial"
    )
