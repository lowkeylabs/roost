from __future__ import annotations

import pytest

from owlroost.schema.registry import (
    SchemaRegistry,
)
from owlroost.schema.specs import (
    FieldSpec,
)


def test_register_and_get():
    reg = SchemaRegistry()

    field = FieldSpec(
        name="x",
    )

    reg.register(field)

    assert reg.get("x") is field


def test_exists():
    reg = SchemaRegistry()

    reg.register(
        FieldSpec(
            name="x",
        )
    )

    assert reg.exists("x")
    assert not reg.exists("y")


def test_duplicate_registration_fails():
    reg = SchemaRegistry()

    reg.register(
        FieldSpec(
            name="x",
        )
    )

    with pytest.raises(
        ValueError,
    ):
        reg.register(
            FieldSpec(
                name="x",
            )
        )


def test_missing_lookup_fails():
    reg = SchemaRegistry()

    with pytest.raises(
        KeyError,
    ):
        reg.get("missing")
