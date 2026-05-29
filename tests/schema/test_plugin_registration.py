# tests/schema/test_plugin_registration.py

from __future__ import annotations

from owlroost.schema.bootstrap import (
    build_registry,
)
from owlroost.schema.specs import (
    FieldSpec,
)

# =========================================================
# Registry Build
# =========================================================


def test_all_schema_plugins_register():
    """
    Ensure all schema plugins successfully
    register into the unified ontology
    registry.

    This acts as a high-level integration
    contract test across all plugins.
    """

    registry = build_registry()

    fields = list(registry.all())

    assert fields


# =========================================================
# Ontology Type Integrity
# =========================================================


def test_all_registered_fields_are_fieldspec():
    """
    Ensure all registered ontology entries
    are canonical FieldSpec instances.
    """

    registry = build_registry()

    for field in registry.all():
        assert isinstance(
            field,
            FieldSpec,
        )


# =========================================================
# Modern Ontology Vocabulary
# =========================================================


def test_no_legacy_level_attribute():
    """
    Prevent regressions back to the legacy
    ontology vocabulary.

    Field ontology should use:

        materialization_level

    rather than:

        level
    """

    registry = build_registry()

    for field in registry.all():
        assert not hasattr(
            field,
            "level",
        )


# =========================================================
# Materialization Integrity
# =========================================================


def test_all_fields_have_materialization_level():
    """
    Every ontology field should declare
    analytical materialization semantics.
    """

    registry = build_registry()

    for field in registry.all():
        assert field.materialization_level is not None


# =========================================================
# Canonical Identity Integrity
# =========================================================


def test_field_names_are_unique():
    """
    Canonical ontology field names must be
    globally unique.
    """

    registry = build_registry()

    names = [field.name for field in registry.all()]

    assert len(names) == len(set(names))


# =========================================================
# Source Integrity
# =========================================================


def test_all_fields_have_source():
    """
    Every ontology field should declare
    semantic source ownership.
    """

    registry = build_registry()

    for field in registry.all():
        assert field.source


# =========================================================
# Path Integrity
# =========================================================


def test_all_fields_have_path():
    """
    Every ontology field should declare
    canonical lookup path semantics.
    """

    registry = build_registry()

    for field in registry.all():
        assert field.path is not None


# =========================================================
# Description Integrity
# =========================================================


def test_all_fields_have_description():
    """
    Ensure ontology fields expose
    explainability metadata.
    """

    registry = build_registry()

    for field in registry.all():
        assert field.description is not None
