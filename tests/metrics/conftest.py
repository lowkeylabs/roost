from __future__ import annotations

import pytest

from owlroost.metrics.specs import (
    MetricSpec,
)


@pytest.fixture
def sample_metric():

    return MetricSpec(
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
