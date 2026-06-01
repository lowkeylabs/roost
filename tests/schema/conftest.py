from __future__ import annotations

import pytest

from owlroost.schema.bootstrap import (
    build_schema_registry,
)


@pytest.fixture
def schema_registry():
    """
    Fully initialized schema registry.
    """

    return build_schema_registry()
