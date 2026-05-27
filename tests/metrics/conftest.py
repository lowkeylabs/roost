from __future__ import annotations

import pytest

from owlroost.metrics.specs import (
    MetricFieldSpec,
)


@pytest.fixture
def sample_metric():

    return MetricFieldSpec(
        name="timing.elapsed_seconds",
        owner="ROOST",
        semantic_domain="execution",
        value_origin="roost-computed",
        projection_kind="canonical",
        materialization_level="trial",
        dtype=float,
        aggregatable=True,
        default_aggregates=[
            "mean",
            "median",
        ],
    )
