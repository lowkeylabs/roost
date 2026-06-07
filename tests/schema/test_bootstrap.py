from __future__ import annotations

from owlroost.schema.bootstrap import (
    build_schema_registry,
)
from owlroost.schema.registry import (
    SchemaRegistry,
)


def test_build_schema_registry():
    """
    Registry boots successfully.
    """

    reg = build_schema_registry()

    assert isinstance(
        reg,
        SchemaRegistry,
    )

    assert len(reg) > 0


def test_registry_contains_owl_fields(
    schema_registry,
):
    """
    OWL bridge fields are present.
    """

    owl_fields = [
        f
        for f in schema_registry
        if getattr(
            f,
            "owner",
            None,
        )
        == "OWL"
    ]

    assert owl_fields
