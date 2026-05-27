from __future__ import annotations

import pytest

from owlroost.metrics.registry import (
    MetricsRegistry,
)

from owlroost.metrics.specs import (
    MetricFieldSpec,
)


@pytest.fixture
def metrics_registry():

    reg = MetricsRegistry()

    reg.register(
        MetricFieldSpec(
            name="timing.elapsed_seconds",
            owner="ROOST",
            semantic_domain="execution",
            value_origin="roost-computed",
            projection_kind="canonical",
            materialization_level="trial",
            dtype=float,
            aggregatable=True,
            default_aggregates=[
                "median",
                "p90",
            ],
        )
    )

    return reg


@pytest.fixture
def sample_trial_rows():

    return [
        {
            "_metrics": {
                "timing.elapsed_seconds": 1.0,
            }
        },
        {
            "_metrics": {
                "timing.elapsed_seconds": 2.0,
            }
        },
        {
            "_metrics": {
                "timing.elapsed_seconds": 3.0,
            }
        },
    ]
