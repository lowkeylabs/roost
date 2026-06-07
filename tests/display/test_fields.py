# tests/display/test_fields.py

from __future__ import annotations

from owlroost.display.fields import (
    register_all_display_fields,
)
from owlroost.display.registry import (
    DisplayRegistry,
)

# =========================================================
# Fixtures
# =========================================================


def build_registry() -> DisplayRegistry:
    reg = DisplayRegistry()

    register_all_display_fields(
        reg,
    )

    return reg


# =========================================================
# Loading
# =========================================================


def test_example_fields_load():
    reg = build_registry()

    expected = {
        "example.bequest_overlay",
        "example.runtime_metric",
        "example.synthetic",
        "example.composed",
        "example.hidden",
        "example.semantic",
        "example.multiple_profiles",
    }

    for field_name in expected:
        assert reg.has_display_field(
            field_name,
        )


def test_testing_fields_load():
    reg = build_registry()

    expected = {
        "testing.scalar",
        "testing.string",
        "testing.boolean",
        "testing.composed",
        "testing.semantic",
    }

    for field_name in expected:
        assert reg.has_display_field(
            field_name,
        )


# =========================================================
# Catalog Declarations
# =========================================================


def test_example_synthetic_field_has_catalog_declaration():
    """
    Synthetic display variables should
    create semantic catalog declarations.
    """

    reg = build_registry()

    field = reg.get_display_field(
        "example.synthetic",
    )

    declaration = field.catalog_declaration

    assert declaration is not None

    assert declaration.owner == "ROOST"

    assert declaration.semantic_domain == "execution"

    assert declaration.value_origin == "roost-computed"

    assert declaration.projection_kind == "synthetic"


def test_testing_semantic_field_has_explicit_ontology():
    """
    Explicit ontology declarations
    should be preserved.
    """

    reg = build_registry()

    field = reg.get_display_field(
        "testing.semantic",
    )

    declaration = field.catalog_declaration

    assert declaration is not None

    assert declaration.owner == "ROOST"

    assert declaration.semantic_domain

    assert declaration.value_origin

    assert declaration.projection_kind


def test_composed_field_has_lineage():
    """
    Lineage metadata should be stored
    within the catalog declaration.
    """

    reg = build_registry()

    field = reg.get_display_field(
        "example.composed",
    )

    declaration = field.catalog_declaration

    assert declaration is not None

    assert declaration.derived_from

    assert "example.synthetic" in declaration.derived_from

    assert "example.runtime_metric" in declaration.derived_from


# =========================================================
# Profiles
# =========================================================


def test_multiple_profiles_exist():
    reg = build_registry()

    field = reg.get_display_field(
        "example.multiple_profiles",
    )

    assert "table" in field.profiles

    assert "pivot" in field.profiles

    assert "export" in field.profiles


def test_hidden_field_is_hidden():
    reg = build_registry()

    field = reg.get_display_field(
        "example.hidden",
    )

    profile = field.profiles["table"]

    assert profile.visible is False
