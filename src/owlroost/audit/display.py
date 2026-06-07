# src/owlroost/audit/display.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Display subsystem audit.

Notes
-----
Validates display-layer invariants.

Display owns:

    - labels
    - formatting
    - alignment
    - grouping
    - views
    - presentation composition
    - mode participation
    - renderer-facing metadata

Display does NOT own:

    - ontology
    - semantic identity
    - provenance
    - lineage

Those responsibilities belong to:

    audit_catalog()
    audit_ontology()
"""

from __future__ import annotations

from owlroost.display.bootstrap import (
    build_display_registry,
)
from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)
from owlroost.schema.bootstrap import (
    build_schema_registry,
)


def audit_display() -> int:
    """
    Audit display subsystem integrity.
    """

    print("DISPLAY")
    print("-------")

    failures = 0

    # =====================================================
    # Registries
    # =====================================================

    schema_registry = build_schema_registry()

    metrics_registry = build_metrics_registry()

    display_registry = build_display_registry(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
    )

    # =====================================================
    # Fields
    # =====================================================

    print("FIELDS")
    print("------")

    fields = display_registry.all_display_fields()

    if not fields:
        failures += 1
        print("no display fields loaded")
    else:
        print(f"Fields: {len(fields)}")

    # =====================================================
    # Duplicate Display Fields
    # =====================================================

    print()
    print("FIELD UNIQUENESS")
    print("----------------")

    field_names = [field.field_name for field in fields]

    duplicates = sorted(name for name in set(field_names) if field_names.count(name) > 1)

    if duplicates:
        failures += len(duplicates)

        for name in duplicates:
            print(f"duplicate display field: {name}")
    else:
        print("OK")

    # =====================================================
    # Groups
    # =====================================================

    print()
    print("GROUPS")
    print("------")

    groups = display_registry.all_groups()

    print(f"Groups: {len(groups)}")

    # =====================================================
    # Views
    # =====================================================

    print()
    print("VIEWS")
    print("-----")

    views = display_registry.all_views()

    print(f"Views: {len(views)}")

    # =====================================================
    # Fixture Sanity
    # =====================================================

    print()
    print("FIXTURES")
    print("--------")

    expected_fields = {
        "testing.scalar",
        "testing.string",
        "testing.boolean",
        "testing.composed",
        "testing.semantic",
    }

    loaded_field_names = {field.field_name for field in fields}

    missing = sorted(expected_fields - loaded_field_names)

    if missing:
        failures += len(missing)

        for name in missing:
            print(f"missing fixture field: {name}")
    else:
        print("OK")

    # =====================================================
    # Summary
    # =====================================================

    print()
    print("SUMMARY")
    print("-------")

    print(f"Display fields:    {len(fields)}")

    print(f"Groups:            {len(groups)}")

    print(f"Views:             {len(views)}")

    print(f"Total issues:      {failures}")

    print()

    return failures
