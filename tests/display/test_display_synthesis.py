from __future__ import annotations

from owlroost.display.registry import (
    DisplayRegistry,
)

from owlroost.metrics.aggregation.aggregate_metrics import (
    register_aggregate_display_fields,
)


def test_aggregate_display_fields_registered(
    metrics_registry,
):

    reg = DisplayRegistry()

    register_aggregate_display_fields(
        reg,
        metrics_registry,
    )

    assert reg.has_display_field(
        "timing.elapsed_seconds__median"
    )

    assert reg.has_display_field(
        "timing.elapsed_seconds__p90"
    )


def test_aggregate_display_field_has_profiles(
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

    assert field.profiles
