from __future__ import annotations

import pytest

from owlroost.schema.specs import (
    FieldSpec,
)


@pytest.fixture
def sample_field():

    return FieldSpec(
        name="solver_options.bequest",
        dtype=float,
        path=(
            "solver_options",
            "bequest",
        ),
        owner="OWL",
        semantic_domain="decision",
        value_origin="user-specified",
        materialization_level="run",
        description="Minimum bequest constraint.",
    )
