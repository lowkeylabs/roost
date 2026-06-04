# src/owlroost/audit/catalog.py

"""
Catalog consistency audit.

Notes
-----
Validates structural invariants of the
canonical semantic catalog.

The catalog owns:

    - canonical semantic identity
    - provenance evolution
    - lineage relationships
    - graph structure

The catalog does NOT validate:

    - ontology completeness
    - display formatting
    - renderer behavior

Those belong to:

    audit_ontology()
    audit_display()
"""

from __future__ import annotations

from collections import Counter

from owlroost.catalog.service import load_catalog
from owlroost.display.bootstrap import build_display_registry
from owlroost.metrics.bootstrap import build_metrics_registry
from owlroost.schema.bootstrap import build_schema_registry

# =========================================================
# Audit
# =========================================================


def audit_catalog() -> int:
    """
    Execute catalog consistency audit.

    Returns
    -------
    int
        Number of catalog violations.
    """

    print("CATALOG")
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
    # Catalog
    # =====================================================

    rows = load_catalog(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
        display_registry=display_registry,
    )

    identity_failures = 0
    required_failures = 0
    lineage_failures = 0
    node_failures = 0

    # =====================================================
    # Semantic Identity
    # =====================================================

    print("SEMANTIC IDENTITIES")
    print("-------------------")

    counts = Counter(row.get("field_name") for row in rows)

    duplicates = sorted(field_name for field_name, count in counts.items() if count > 1)

    for field_name in duplicates:
        failures += 1
        identity_failures += 1

        print(f"duplicate semantic identity: {field_name}")

    if identity_failures == 0:
        print("OK")

    # =====================================================
    # Required Catalog Fields
    # =====================================================

    print()
    print("REQUIRED FIELDS")
    print("---------------")

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

                print(f"{field_name}: missing {required}")

    if required_failures == 0:
        print("OK")

    # =====================================================
    # Lineage Integrity
    # =====================================================

    print()
    print("LINEAGE")
    print("-------")

    known_fields = {row["field_name"] for row in rows if row.get("field_name")}

    for row in rows:
        field_name = row.get(
            "field_name",
            "<unknown>",
        )

        for dependency in row.get(
            "derived_from",
            [],
        ):
            if dependency not in known_fields:
                failures += 1
                lineage_failures += 1

                print(f"{field_name}: derived_from -> {dependency} not found")

        for dependency in row.get(
            "expands_to",
            [],
        ):
            if dependency not in known_fields:
                failures += 1
                lineage_failures += 1

                print(f"{field_name}: expands_to -> {dependency} not found")

    if lineage_failures == 0:
        print("OK")

    # =====================================================
    # Node Types
    # =====================================================

    print()
    print("NODE TYPES")
    print("----------")

    valid_node_types = {
        "variable",
        "overlay",
    }

    for row in rows:
        field_name = row.get(
            "field_name",
            "<unknown>",
        )

        node_type = row.get(
            "node_type",
        )

        if node_type is not None and str(node_type) not in valid_node_types:
            failures += 1
            node_failures += 1

            print(f"{field_name}: invalid node_type {node_type!r}")

    if node_failures == 0:
        print("OK")

    # =====================================================
    # Distributions
    # =====================================================

    print()
    print("NODE TYPE DISTRIBUTION")
    print("----------------------")

    node_counts = Counter(
        str(
            row.get(
                "node_type",
                "<missing>",
            )
        )
        for row in rows
    )

    for node_type in sorted(
        node_counts,
    ):
        print(f"{node_type:<20}{node_counts[node_type]}")

    print()
    print("PROVENANCE DEPTHS")
    print("-----------------")

    depth_counts = Counter(
        row.get(
            "provenance_depth",
            0,
        )
        for row in rows
    )

    for depth in sorted(
        depth_counts,
    ):
        print(f"{depth:<20}{depth_counts[depth]}")

    # =====================================================
    # Summary
    # =====================================================

    print()
    print("SUMMARY")
    print("-------")

    print(f"Catalog rows:        {len(rows)}")

    print(f"Unique identities:   {len(counts)}")

    print(f"Identity issues:     {identity_failures}")

    print(f"Required fields:     {required_failures}")

    print(f"Lineage issues:      {lineage_failures}")

    print(f"Node type issues:    {node_failures}")

    print(f"Total issues:        {failures}")

    print()

    return failures
