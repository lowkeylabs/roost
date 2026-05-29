from __future__ import annotations

import pytest

from owlroost.schema.registry import (
    SchemaRegistry,
)
from owlroost.schema.specs import (
    FieldSpec,
)

# =========================================================
# Registration
# =========================================================


def test_registry_register_and_get(
    sample_field,
):
    reg = SchemaRegistry()

    reg.register(sample_field)

    out = reg.get("solver_options.bequest")

    assert out is sample_field


def test_registry_duplicate_registration_raises():
    reg = SchemaRegistry()

    field = FieldSpec(
        name="solver_options.bequest",
    )

    reg.register(field)

    with pytest.raises(ValueError):
        reg.register(field)


# =========================================================
# Lookup
# =========================================================


def test_registry_missing_lookup_raises():
    reg = SchemaRegistry()

    with pytest.raises(KeyError):
        reg.get("missing.field")


def test_registry_exists():
    reg = SchemaRegistry()

    field = FieldSpec(
        name="solver_options.bequest",
    )

    reg.register(field)

    assert reg.exists("solver_options.bequest")

    assert not reg.exists("missing.field")


# =========================================================
# Iteration
# =========================================================


def test_registry_len():
    reg = SchemaRegistry()

    reg.register(FieldSpec(name="a"))

    reg.register(FieldSpec(name="b"))

    assert len(reg) == 2


def test_registry_contains():
    reg = SchemaRegistry()

    reg.register(FieldSpec(name="a"))

    assert "a" in reg

    assert "b" not in reg


def test_registry_names():
    reg = SchemaRegistry()

    reg.register(FieldSpec(name="a"))

    reg.register(FieldSpec(name="b"))

    names = set(reg.names())

    assert names == {
        "a",
        "b",
    }


def test_registry_items():
    reg = SchemaRegistry()

    reg.register(FieldSpec(name="a"))

    items = dict(reg.items())

    assert "a" in items


def test_registry_iteration():
    reg = SchemaRegistry()

    reg.register(FieldSpec(name="a"))

    reg.register(FieldSpec(name="b"))

    names = {f.name for f in reg}

    assert names == {
        "a",
        "b",
    }
