# src/owlroost/audit/display.py

"""
Display subsystem audit.

Notes
-----
Validates display-layer architecture,
overlay correctness, and fixture loading.

Model B2 Architecture
---------------------

Schema Registry
    owns semantic variables

Metrics Registry
    owns semantic variables

Catalog
    owns graph structure

Display
    owns presentation overlays

Display Responsibilities
------------------------

Display owns:

    - labels
    - formatting
    - alignment
    - grouping
    - views

Display does NOT own:

    - schema ontology
    - metrics ontology
    - catalog graph structure

Display fields therefore fall into two
categories:

    1. Ontology-backed overlays
       (linked to schema/metrics)

    2. Synthetic display fields
       (carry ontology directly)

Audit Responsibilities
----------------------

This audit validates:

    - ontology-backed field linkage
    - synthetic ontology completeness
    - synthetic lineage metadata
    - field autoloading
    - group autoloading
    - view autoloading
    - testing/example fixtures

Catalog graph correctness is validated by:

    audit_catalog()

Ontology completeness is validated by:

    audit_ontology()
"""

from __future__ import annotations

import ast
from pathlib import Path

from owlroost.display.bootstrap import (
    build_display_registry,
)
from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)
from owlroost.schema.bootstrap import (
    build_schema_registry,
)

# =========================================================
# Discovery Paths
# =========================================================

DISPLAY_ROOT = Path(__file__).parents[1] / "display"

FIELDS_DIR = DISPLAY_ROOT / "fields"

GROUPS_DIR = DISPLAY_ROOT / "groups"

VIEWS_DIR = DISPLAY_ROOT / "views"

# =========================================================
# Field Discovery
# =========================================================


def build_field_source_map() -> dict[str, str]:
    """
    Discover display-owned fields.

    Returns
    -------
    field_name -> filename
    """

    mapping: dict[str, str] = {}

    if not FIELDS_DIR.exists():
        return mapping

    for path in sorted(FIELDS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue

        try:
            tree = ast.parse(
                path.read_text(),
                filename=str(path),
            )

        except Exception:
            continue

        for node in ast.walk(tree):
            if not isinstance(
                node,
                ast.Call,
            ):
                continue

            func = node.func

            if not (
                isinstance(
                    func,
                    ast.Attribute,
                )
                and func.attr == "field"
            ):
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
                mapping[first_arg.value] = path.name

    return mapping


# =========================================================
# Formatting
# =========================================================


def emit_issue(
    *,
    field_name: str,
    source_file: str,
    message: str,
):
    print(f"{field_name} ({source_file}): {message}")


# =========================================================
# Audit
# =========================================================


def audit_display() -> int:
    print("DISPLAY")
    print("-------")

    failures = 0

    # =====================================================
    # Source Discovery
    # =====================================================

    source_map = build_field_source_map()

    # =====================================================
    # Registries
    # =====================================================

    schema_registry = build_schema_registry()

    metrics_registry = build_metrics_registry()

    display_registry = build_display_registry(
        schema_registry,
        metrics_registry,
    )

    # =====================================================
    # Counts
    # =====================================================

    total_fields = 0

    ontology_backed = 0

    synthetic_fields = 0

    display_owned = 0

    schema_backed = 0

    metrics_backed = 0

    # =====================================================
    # Ontology Audit
    # =====================================================

    print("ONTOLOGY")
    print("--------")

    ontology_issues = 0

    for field in display_registry.all_display_fields():
        total_fields += 1

        source_file = source_map.get(
            field.field_name,
            "<generated>",
        )

        # =============================================
        # Synthetic Display Fields
        # =============================================

        if getattr(
            field,
            "is_synthetic",
            False,
        ):
            synthetic_fields += 1
            display_owned += 1

            missing: list[str] = []

            for attr in (
                "owner",
                "semantic_domain",
                "value_origin",
                "projection_kind",
            ):
                if not getattr(
                    field,
                    attr,
                    None,
                ):
                    missing.append(attr)

            if missing:
                ontology_issues += 1

                emit_issue(
                    field_name=(field.field_name),
                    source_file=(source_file),
                    message=("synthetic field missing " + ", ".join(missing)),
                )

            continue

        # =============================================
        # Ontology-backed Fields
        # =============================================

        ontology_backed += 1

        if field.ontology_field is None:
            ontology_issues += 1

            emit_issue(
                field_name=(field.field_name),
                source_file=(source_file),
                message=("missing ontology link"),
            )

            continue

        defined_in = getattr(
            field.ontology_field,
            "defined_in",
            None,
        )

        if defined_in == "OWL":
            schema_backed += 1

        elif defined_in:
            metrics_backed += 1

    if ontology_issues == 0:
        print("OK")

    failures += ontology_issues

    # =====================================================
    # Synthetic Lineage
    # =====================================================

    print()
    print("SYNTHETIC LINEAGE")
    print("-----------------")

    lineage_issues = 0

    for field in display_registry.all_display_fields():
        if not getattr(
            field,
            "is_synthetic",
            False,
        ):
            continue

        source_file = source_map.get(
            field.field_name,
            "<generated>",
        )

        if field.display_fn and not field.derived_from:
            lineage_issues += 1

            emit_issue(
                field_name=(field.field_name),
                source_file=(source_file),
                message=("display_fn present but derived_from missing"),
            )

    if lineage_issues == 0:
        print("OK")

    failures += lineage_issues

    # =====================================================
    # Field Sources
    # =====================================================

    print()
    print("FIELD SOURCES")
    print("-------------")

    print(f"Schema-backed:      {schema_backed}")

    print(f"Metrics-backed:     {metrics_backed}")

    print(f"Display-owned:      {display_owned}")

    # =====================================================
    # Groups
    # =====================================================

    print()
    print("GROUPS")
    print("------")

    group_names = list(display_registry.all_group_names())

    if group_names:
        print(f"Groups: {len(group_names)}")

    else:
        failures += 1

        print("no groups loaded")

    # =====================================================
    # Views
    # =====================================================

    print()
    print("VIEWS")
    print("-----")

    view_count = 0

    for level in display_registry.all_levels():
        view_count += len(display_registry.all_view_names(level))

    if view_count:
        print(f"Views: {view_count}")

    else:
        failures += 1

        print("no views loaded")

    # =====================================================
    # Fixtures
    # =====================================================

    print()
    print("FIXTURES")
    print("--------")

    fixture_issues = 0

    expected_fields = {
        "testing.scalar",
        "example.synthetic",
    }

    for field_name in expected_fields:
        if not (display_registry.has_display_field(field_name)):
            fixture_issues += 1

            print(f"{field_name}: missing")

    expected_groups = {
        "testing.expansion",
        "example.summary",
    }

    for group_name in expected_groups:
        if not (display_registry.has_group(group_name)):
            fixture_issues += 1

            print(f"{group_name}: missing")

    expected_views = [
        (
            "case",
            "testing-fixture",
        ),
        (
            "case",
            "example-summary",
        ),
    ]

    for (
        level,
        view_name,
    ) in expected_views:
        if not (
            display_registry.has_view(
                level,
                view_name,
            )
        ):
            fixture_issues += 1

            print(f"{level}/{view_name}: missing")

    if fixture_issues == 0:
        print("OK")

    failures += fixture_issues

    # =====================================================
    # Summary
    # =====================================================

    print()
    print("SUMMARY")
    print("-------")

    print(f"Display fields:     {total_fields}")

    print(f"Ontology-backed:    {ontology_backed}")

    print(f"Synthetic:          {synthetic_fields}")

    print(f"Discovered fields:  {len(source_map)}")

    print(f"Issues:             {failures}")

    print()

    return failures
