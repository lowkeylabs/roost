from __future__ import annotations

import pytest

from owlroost.metrics.registry import (
    MetricsRegistry,
)
from owlroost.metrics.specs import (
    MetricFieldSpec,
)


# =========================================================
# Registration
# =========================================================


def test_registry_register_and_get(
    sample_metric,
):

    reg = MetricsRegistry()

    reg.register(
        sample_metric
    )

    out = reg.get(
        "timing.elapsed_seconds"
    )

    assert out is sample_metric


def test_duplicate_metric_registration_raises():

    reg = MetricsRegistry()

    metric = MetricFieldSpec(
        name="timing.elapsed_seconds",
    )

    reg.register(metric)

    with pytest.raises(
        ValueError
    ):
        reg.register(metric)


# =========================================================
# Lookup
# =========================================================


def test_registry_missing_lookup_raises():

    reg = MetricsRegistry()

    with pytest.raises(
        KeyError
    ):
        reg.get(
            "missing.metric"
        )


def test_registry_exists():

    reg = MetricsRegistry()

    metric = MetricFieldSpec(
        name="timing.elapsed_seconds",
    )

    reg.register(metric)

    assert reg.exists(
        "timing.elapsed_seconds"
    )

    assert not reg.exists(
        "missing.metric"
    )


# =========================================================
# Iteration
# =========================================================


def test_registry_len():

    reg = MetricsRegistry()

    reg.register(
        MetricFieldSpec(name="a")
    )

    reg.register(
        MetricFieldSpec(name="b")
    )

    assert len(reg) == 2


def test_registry_contains():

    reg = MetricsRegistry()

    reg.register(
        MetricFieldSpec(name="a")
    )

    assert "a" in reg

    assert "b" not in reg


def test_registry_names():

    reg = MetricsRegistry()

    reg.register(
        MetricFieldSpec(name="a")
    )

    reg.register(
        MetricFieldSpec(name="b")
    )

    names = set(
        reg.names()
    )

    assert names == {
        "a",
        "b",
    }


def test_registry_items():

    reg = MetricsRegistry()

    reg.register(
        MetricFieldSpec(name="a")
    )

    items = dict(
        reg.items()
    )

    assert "a" in items


def test_registry_iteration():

    reg = MetricsRegistry()

    reg.register(
        MetricFieldSpec(name="a")
    )

    reg.register(
        MetricFieldSpec(name="b")
    )

    names = {
        m.name
        for m in reg
    }

    assert names == {
        "a",
        "b",
    }
