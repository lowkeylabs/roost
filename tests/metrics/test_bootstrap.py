from __future__ import annotations

from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)


# =========================================================
# Bootstrap
# =========================================================


def test_metrics_registry_bootstrap():

    reg = build_metrics_registry()

    assert reg.exists(
        "timing.elapsed_seconds"
    )

    assert reg.exists(
        "trial.completed"
    )

    assert reg.exists(
        "financial.spending.total.today"
    )


def test_aggregate_metrics_synthesized():

    reg = build_metrics_registry()

    assert reg.exists(
        "timing.elapsed_seconds__median"
    )

    assert reg.exists(
        "financial.spending.total.today__p90"
    )
