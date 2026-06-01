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
# Ontology
# =========================================================


def test_example_synthetic_field_has_ontology():
    reg = build_registry()

    field = reg.get_display_field(
        "example.synthetic",
    )

    assert field.owner
    assert field.semantic_domain
    assert field.value_origin
    assert field.projection_kind
    assert field.materialization_level


def test_testing_semantic_field_has_explicit_ontology():
    reg = build_registry()

    field = reg.get_display_field(
        "testing.semantic",
    )

    assert field.owner == "ROOST"
    assert field.semantic_domain
    assert field.value_origin
    assert field.projection_kind


# =========================================================
# Lineage
# =========================================================


def test_composed_field_has_lineage():
    reg = build_registry()

    field = reg.get_display_field(
        "example.composed",
    )

    assert field.derived_from

    assert "example.synthetic" in field.derived_from

    assert "example.runtime_metric" in field.derived_from


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
