# src/owlroost/audit/ontology.py

"""
Ontology consistency audit.

Notes
-----
Validates ontology invariants across the
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

Ontology Responsibilities
-------------------------

This audit validates:

    - semantic ontology completeness
    - aggregate semantic consistency

The goal is to identify ontology gaps
early and point directly to the plugin
responsible for the missing metadata.
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

# =========================================================
# Helpers
# =========================================================


def _defined_in(
    row,
) -> str:
    """
    Best-effort source attribution.

    Helps identify which plugin likely
    owns a missing ontology field.
    """

    value = row.get("defined_in")

    if value:
        return str(value)

    source = row.get("source")

    if source:
        return str(source)

    return "unknown"


# =========================================================
# Audit
# =========================================================


def audit_ontology() -> int:
    print("ONTOLOGY")
    print("--------")

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
    # Counters
    # =====================================================

    semantic_failures = 0
    aggregate_failures = 0

    # =====================================================
    # Semantic Completeness
    # =====================================================

    print("SEMANTIC COMPLETENESS")
    print("---------------------")

    required_fields = [
        "owner",
        "semantic_domain",
        "value_origin",
        "projection_kind",
        "analytic_kind",
        "materialization_level",
    ]

    for row in rows:
        field_name = row.get(
            "field_name",
            "<unknown>",
        )

        missing = []

        for required in required_fields:
            if row.get(required) is None:
                missing.append(required)

        if missing:
            failures += 1
            semantic_failures += 1

            print(f"{field_name}: missing {', '.join(missing)} [defined_in={_defined_in(row)}]")

    if semantic_failures == 0:
        print("OK")

    # =====================================================
    # Aggregate Semantics
    # =====================================================

    print()
    print("AGGREGATE SEMANTICS")
    print("-------------------")

    for row in rows:
        projection_kind = row.get("projection_kind")

        analytic_kind = row.get("analytic_kind")

        field_name = row.get(
            "field_name",
            "<unknown>",
        )

        if projection_kind == "aggregate" and analytic_kind not in {
            "aggregate",
            "distributional",
        }:
            failures += 1
            aggregate_failures += 1

            print(
                f"{field_name}: "
                "aggregate projection "
                "missing aggregate "
                "analytic_kind "
                f"({analytic_kind!r})"
            )

    if aggregate_failures == 0:
        print("OK")

    # =====================================================
    # Ontology Distribution
    # =====================================================

    print()
    print("OWNERS")
    print("------")

    owner_counts = Counter(
        row.get(
            "owner",
            "<missing>",
        )
        for row in rows
    )

    for owner in sorted(owner_counts):
        print(f"{str(owner):<20}{owner_counts[owner]}")

    # =====================================================
    # Summary
    # =====================================================

    print()
    print("SUMMARY")
    print("-------")

    print(f"Catalog rows:        {len(rows)}")

    print(f"Semantic issues:     {semantic_failures}")

    print(f"Aggregate issues:    {aggregate_failures}")

    print(f"Total issues:        {failures}")

    print()

    return failures
