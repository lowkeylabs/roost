# src/owlroost/audit/catalog.py

"""
Catalog consistency audit.

Notes
-----
Validates structural invariants of the
canonical semantic catalog.

This audit operates on catalog rows rather
than CatalogSpec objects.

Model B2 Architecture
---------------------

Schema Registry
    owns semantic variables

Metrics Registry
    owns semantic variables

Catalog
    owns semantic identity

Display
    owns presentation overlays

Catalog Responsibilities
------------------------

Catalog validates:

    - semantic identity uniqueness
    - required catalog fields
    - catalog row completeness
    - node type assignment

Catalog does NOT validate:

    - ontology completeness
    - display overlays
    - namespace containers

Those responsibilities belong to:

    audit_ontology()
    audit_display()

Architectural Invariants
------------------------

1. Exactly one catalog row exists for each:

       field_name

2. Canonical semantic identity is unique.

3. Every catalog row advertises:

       field_name
       node_type

4. Catalog rows represent semantic
   entities rather than TOML containers.
"""

from __future__ import annotations

from collections import Counter

from owlroost.catalog.service import (
    load_catalog,
)
from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)
from owlroost.schema.bootstrap import (
    build_schema_registry,
)


def audit_catalog() -> int:
    print("CATALOG")
    print("-------")

    failures = 0

    # =====================================================
    # Canonical Registries
    # =====================================================

    schema_registry = build_schema_registry()

    metrics_registry = build_metrics_registry()

    # =====================================================
    # Catalog
    # =====================================================

    rows = load_catalog(
        schema_registry=(schema_registry),
        metrics_registry=(metrics_registry),
    )

    # =====================================================
    # Semantic Identity Audit
    # =====================================================

    print("SEMANTIC IDENTITIES")
    print("-------------------")

    counts = Counter(row.get("field_name") for row in rows)

    duplicates = sorted(
        field_name
        for (
            field_name,
            count,
        ) in counts.items()
        if count > 1
    )

    for field_name in duplicates:
        failures += 1

        print(f"duplicate semantic identity: {field_name}")

    if not duplicates:
        print("OK")

    # =====================================================
    # Required Fields Audit
    # =====================================================

    print()
    print("REQUIRED FIELDS")
    print("---------------")

    required_failures = 0

    required_fields = [
        "field_name",
        "node_type",
    ]

    for row in rows:
        field_name = row.get(
            "field_name",
            "<unknown>",
        )

        for required in required_fields:
            value = row.get(required)

            if value in {
                None,
                "",
            }:
                failures += 1
                required_failures += 1

                print(f"{field_name}: missing required catalog field {required}")

    if required_failures == 0:
        print("OK")

    # =====================================================
    # Node Type Distribution
    # =====================================================

    print()
    print("NODE TYPES")
    print("----------")

    node_counts = Counter(
        row.get(
            "node_type",
            "<missing>",
        )
        for row in rows
    )

    for node_type in sorted(node_counts):
        print(f"{str(node_type):<20}{node_counts[node_type]}")

    # =====================================================
    # Summary
    # =====================================================

    print()
    print("SUMMARY")
    print("-------")

    print(f"Catalog rows:        {len(rows)}")

    print(f"Unique identities:   {len(counts)}")

    print(f"Node types:          {len(node_counts)}")

    print(f"Total issues:        {failures}")

    print()

    return failures
