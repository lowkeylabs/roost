# src/owlroost/audit/ontology.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Ontology consistency audit.

Notes
-----
Validates ontology invariants across the
canonical semantic catalog.

The ontology audit focuses on:

    - ontology consistency
    - projection semantics
    - analytical semantics
    - provenance coverage
    - metadata distributions

The audit intentionally does NOT require
all ontology dimensions to be populated.

Many ontology dimensions are allowed to
remain unknown during incremental catalog
development.
"""

from __future__ import annotations

from collections import Counter

from owlroost.catalog.service import load_catalog
from owlroost.display.bootstrap import build_display_registry
from owlroost.metrics.bootstrap import build_metrics_registry
from owlroost.schema.bootstrap import build_schema_registry

# =========================================================
# Helpers
# =========================================================


def _defined_in(row) -> str:
    """
    Best-effort source attribution.
    """

    value = row.get("defined_in")

    if value:
        return str(value)

    source = row.get("source")

    if source:
        return str(source)

    return "unknown"


def _print_distribution(
    title,
    rows,
    field_name,
):
    """
    Print ontology distribution.
    """

    print()
    print(title)
    print("-" * len(title))

    counts = Counter(
        row.get(
            field_name,
            "<missing>",
        )
        for row in rows
    )

    for key in sorted(counts):
        print(f"{str(key):<20}{counts[key]}")


# =========================================================
# Audit
# =========================================================


def audit_ontology() -> int:
    """
    Execute ontology consistency audit.

    Returns
    -------
    int
        Number of ontology violations.
    """

    print("ONTOLOGY")
    print("--------")

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

    aggregate_failures = 0
    overlay_failures = 0

    # =====================================================
    # Aggregate Semantics
    # =====================================================

    print("AGGREGATE SEMANTICS")
    print("-------------------")

    for row in rows:
        projection_kind = row.get(
            "projection_kind",
        )

        analytic_kind = row.get(
            "analytic_kind",
        )

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
                f"aggregate projection "
                f"requires aggregate/distributional "
                f"analytic_kind "
                f"(found {analytic_kind!r})"
            )

    if aggregate_failures == 0:
        print("OK")

    # =====================================================
    # Overlay Ownership
    # =====================================================

    print()
    print("OVERLAY OWNERSHIP")
    print("-----------------")

    for row in rows:
        node_type = row.get(
            "node_type",
        )

        owner = row.get(
            "owner",
        )

        field_name = row.get(
            "field_name",
            "<unknown>",
        )

        if node_type == "overlay" and owner not in {
            "ROOST",
            None,
        }:
            failures += 1
            overlay_failures += 1

            print(f"{field_name}: overlay owned by {owner!r}")

    if overlay_failures == 0:
        print("OK")

    # =====================================================
    # Provenance Coverage
    # =====================================================

    print()
    print("PROVENANCE")
    print("----------")

    provenance_missing = 0

    for row in rows:
        field_name = row.get(
            "field_name",
            "<unknown>",
        )

        depth = row.get(
            "provenance_depth",
        )

        if depth in {
            None,
            0,
        }:
            provenance_missing += 1

            print(f"{field_name}: missing provenance")

    if provenance_missing == 0:
        print("OK")

    # =====================================================
    # Ontology Distributions
    # =====================================================

    _print_distribution(
        "OWNERS",
        rows,
        "owner",
    )

    _print_distribution(
        "SEMANTIC DOMAINS",
        rows,
        "semantic_domain",
    )

    _print_distribution(
        "VALUE ORIGINS",
        rows,
        "value_origin",
    )

    _print_distribution(
        "PROJECTION KINDS",
        rows,
        "projection_kind",
    )

    _print_distribution(
        "ANALYTIC KINDS",
        rows,
        "analytic_kind",
    )

    _print_distribution(
        "NODE TYPES",
        rows,
        "node_type",
    )

    _print_distribution(
        "MATERIALIZATION LEVELS",
        rows,
        "materialization_level",
    )

    # =====================================================
    # Summary
    # =====================================================

    print()
    print("SUMMARY")
    print("-------")

    print(f"Catalog rows:        {len(rows)}")

    print(f"Aggregate issues:    {aggregate_failures}")

    print(f"Overlay issues:      {overlay_failures}")

    print(f"Provenance missing:  {provenance_missing}")

    print(f"Total issues:        {failures}")

    print()

    return failures
