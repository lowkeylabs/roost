# src/owlroost/audit/display.py

"""
Display subsystem audit.

Notes
-----
Validates structural invariants of the
display subsystem.

Model B2 Architecture
---------------------

Schema
    owns executable input ontology

Metrics
    owns runtime metric ontology

Catalog
    owns canonical semantic identity

Display
    owns presentation identity

Display Responsibilities
------------------------

Display owns:

    - labels
    - formatting
    - alignment
    - grouping
    - views
    - presentation composition

Display may also define synthetic
semantic entities for convenience.

The audit intentionally validates:

    - display field registration
    - synthetic ontology completeness
    - group registration
    - view registration

The audit intentionally does NOT
validate:

    - catalog ontology completeness
    - schema ontology completeness
    - metric ontology completeness

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
    # Ontology
    # =====================================================

    print()
    print("ONTOLOGY")
    print("--------")

    ontology_failures = 0

    for field in fields:
        #
        # Synthetic semantic entities
        # should advertise ontology.
        #

        if not field.is_synthetic:
            continue

        missing = []

        for attr in (
            "owner",
            "semantic_domain",
            "value_origin",
            "projection_kind",
        ):
            if (
                getattr(
                    field,
                    attr,
                    None,
                )
                is None
            ):
                missing.append(
                    attr,
                )

        if missing:
            ontology_failures += 1

            print(f"{field.field_name}: missing {', '.join(missing)}")

    failures += ontology_failures

    if ontology_failures == 0:
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

    field_names = {field.field_name for field in fields}

    missing = sorted(expected_fields - field_names)

    if missing:
        failures += len(
            missing,
        )

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
