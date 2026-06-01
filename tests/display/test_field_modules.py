from __future__ import annotations

import ast
from pathlib import Path

from owlroost.display.fields import (
    register_all_display_fields,
)
from owlroost.display.registry import (
    DisplayRegistry,
)
from owlroost.display.specs import (
    DisplayField,
)

# =========================================================
# Discovery
# =========================================================


FIELDS_DIR = Path(__file__).parents[2] / "src" / "owlroost" / "display" / "fields"


def discover_declared_display_fields() -> set[str]:
    """
    Discover all DisplayField.field(...)
    declarations from display field modules.

    This intentionally inspects source code
    rather than registry state.

    The goal is to ensure every declared field
    is actually registered.
    """

    names: set[str] = set()

    for path in FIELDS_DIR.glob("*.py"):
        if path.name == "__init__.py":
            continue

        tree = ast.parse(
            path.read_text(),
            filename=str(path),
        )

        for node in ast.walk(tree):
            if not isinstance(
                node,
                ast.Call,
            ):
                continue

            func = node.func

            if not (isinstance(func, ast.Attribute) and func.attr == "field"):
                continue

            if not (
                isinstance(
                    func.value,
                    ast.Name,
                )
                and func.value.id == "DisplayField"
            ):
                continue

            if not node.args:
                continue

            first_arg = node.args[0]

            if isinstance(
                first_arg,
                ast.Constant,
            ) and isinstance(
                first_arg.value,
                str,
            ):
                names.add(
                    first_arg.value,
                )

    return names


# =========================================================
# Registration Completeness
# =========================================================


def test_all_declared_display_fields_register():
    """
    Every DisplayField.field(...)
    declaration should appear in the registry.
    """

    reg = DisplayRegistry()

    register_all_display_fields(
        reg,
    )

    declared = discover_declared_display_fields()

    assert declared

    for field_name in sorted(
        declared,
    ):
        assert reg.has_display_field(
            field_name,
        ), f"Display field declared but not registered: {field_name}"


# =========================================================
# Type Integrity
# =========================================================


def test_registered_fields_are_display_fields():
    """
    Every declared field should load
    as a DisplayField instance.
    """

    reg = DisplayRegistry()

    register_all_display_fields(
        reg,
    )

    for field_name in discover_declared_display_fields():
        field = reg.get_display_field(
            field_name,
        )

        assert isinstance(
            field,
            DisplayField,
        )


# =========================================================
# Synthetic Ontology Defaults
# =========================================================


def test_synthetic_fields_have_ontology():
    """
    Synthetic fields should receive
    ontology defaults automatically.
    """

    reg = DisplayRegistry()

    register_all_display_fields(
        reg,
    )

    for field_name in discover_declared_display_fields():
        field = reg.get_display_field(
            field_name,
        )

        if not field.is_synthetic:
            continue

        assert field.owner

        assert field.semantic_domain

        assert field.value_origin

        assert field.projection_kind

        assert field.analytic_kind

        assert field.materialization_level
