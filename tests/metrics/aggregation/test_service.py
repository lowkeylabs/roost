from __future__ import annotations

from owlroost.metrics.aggregation.service import (
    aggregate_rows,
)


def test_aggregate_rows_basic(
    metrics_registry,
    sample_trial_rows,
):

    out = aggregate_rows(
        rows=sample_trial_rows,
        metrics_registry=metrics_registry,
    )

    assert (
        "timing.elapsed_seconds__median"
        in out
    )

    assert (
        "timing.elapsed_seconds__p90"
        in out
    )


def test_aggregate_rows_median_value(
    metrics_registry,
    sample_trial_rows,
):

    out = aggregate_rows(
        rows=sample_trial_rows,
        metrics_registry=metrics_registry,
    )

    assert (
        out[
            "timing.elapsed_seconds__median"
        ]
        == 2.0
    )


def test_aggregate_rows_valid_counts(
    metrics_registry,
    sample_trial_rows,
):

    out = aggregate_rows(
        rows=sample_trial_rows,
        metrics_registry=metrics_registry,
    )

    assert (
        out[
            "timing.elapsed_seconds__median__n_valid"
        ]
        == 3
    )

    assert (
        out[
            "timing.elapsed_seconds__median__n_total"
        ]
        == 3
    )


def test_aggregate_rows_empty_dataset(
    metrics_registry,
):

    out = aggregate_rows(
        rows=[],
        metrics_registry=metrics_registry,
    )

    assert out == {}
