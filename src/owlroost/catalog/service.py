# src/owlroost/catalog/service.py

"""
Catalog semantic services.

Notes
-----
The catalog subsystem owns semantic
identity and ontology synthesis.

Catalog integrates:

    - schema ontology
    - metrics ontology

into a unified collection of canonical
semantic entities.

Catalog returns semantic rows and does
not return renderer-facing structures.
"""

from __future__ import annotations

from copy import deepcopy

from owlroost.catalog.builders import (
    build_metric_rows,
    build_schema_rows,
)
from owlroost.catalog.ontology import (
    AnalyticKind,
    CatalogNodeType,
    Owner,
    ProjectionKind,
    SemanticDomain,
    ValueOrigin,
)

# =========================================================
# Canonical Entity Merge
# =========================================================


def _merge_row(
    entities: dict,
    row: dict,
):
    """
    Merge semantic ontology row into
    canonical catalog entity map.

    Architectural Invariant
    -----------------------
    ROOST maintains exactly one canonical
    semantic identity per field_name.

    Display overlays enrich existing
    semantic identities rather than
    creating competing rows.
    """

    field_name = row["field_name"]

    # =====================================================
    # New Canonical Entity
    # =====================================================

    if field_name not in entities:
        entities[field_name] = deepcopy(row)
        return

    existing = entities[field_name]

    # =====================================================
    # Layer Validation
    # =====================================================

    existing_layer = existing.get("layer")

    incoming_layer = row.get("layer")

    # -----------------------------------------------------
    # Canonical ontology collisions are illegal
    # -----------------------------------------------------

    if existing_layer in {
        "schema",
        "metrics",
    } and incoming_layer in {
        "schema",
        "metrics",
    }:
        raise ValueError(f"Duplicate canonical semantic identity detected: {field_name}")

    # =====================================================
    # Display Overlay Merge
    # =====================================================

    if incoming_layer == "display":
        for key, value in row.items():
            if value is None:
                continue

            if key in {
                "layer",
                "field_name",
            }:
                continue

            existing[key] = value

        overlays = existing.setdefault(
            "_overlay_layers",
            [],
        )

        overlays.append("display")

        return

    # =====================================================
    # Unknown merge behavior
    # =====================================================

    raise ValueError(
        f"Unsupported catalog merge: {field_name} ({existing_layer} <- {incoming_layer})"
    )


# =========================================================
# Catalog Loader
# =========================================================


def load_catalog(
    *,
    schema_registry,
    metrics_registry,
):
    """
    Build unified semantic catalog rows.

    Notes
    -----
    The catalog subsystem acts as semantic
    integration infrastructure layered across:

        - schema ontology
        - metrics ontology
        - aggregation ontology

    The catalog intentionally models:

        canonical semantic entities

    rather than renderer-facing overlays.

    Architectural Invariant
    -----------------------
    Exactly one catalog row exists for each:

        field_name

    Display overlays are intentionally
    excluded from catalog synthesis.

    Display consumes catalog semantics
    downstream.
    """

    entities: dict[
        str,
        dict,
    ] = {}

    # =====================================================
    # Schema Ontology
    # =====================================================

    for row in build_schema_rows(
        schema_registry,
    ):
        _merge_row(
            entities,
            row,
        )

    # =====================================================
    # Metrics Ontology
    # =====================================================

    for row in build_metric_rows(
        metrics_registry,
    ):
        _merge_row(
            entities,
            row,
        )

    # =====================================================
    # Stable Ordering
    # =====================================================

    return sorted(
        entities.values(),
        key=lambda r: (
            r.get("owner") or "",
            r.get("semantic_domain") or "",
            r.get("analytic_kind") or "",
            r.get("projection_kind") or "",
            r.get("node_type") or "",
            r.get("field_name") or "",
        ),
    )


# =========================================================
# Ontology Filters
# =========================================================


def filter_catalog_by_layer(
    rows,
    layer: str,
):
    """
    Filter catalog rows by ontology layer.
    """

    return [row for row in rows if row.get("layer") == layer]


def filter_catalog_by_owner(
    rows,
    owner: Owner,
):
    """
    Filter catalog rows by ontology owner.
    """

    return [row for row in rows if row.get("owner") == owner]


def filter_catalog_by_semantic_domain(
    rows,
    semantic_domain: SemanticDomain,
):
    """
    Filter catalog rows by semantic domain.
    """

    return [row for row in rows if row.get("semantic_domain") == semantic_domain]


def filter_catalog_by_value_origin(
    rows,
    value_origin: ValueOrigin,
):
    """
    Filter catalog rows by value origin.
    """

    return [row for row in rows if row.get("value_origin") == value_origin]


def filter_catalog_by_projection_kind(
    rows,
    projection_kind: ProjectionKind,
):
    """
    Filter catalog rows by analytical
    projection realization.
    """

    return [row for row in rows if row.get("projection_kind") == projection_kind]


def filter_catalog_by_analytic_kind(
    rows,
    analytic_kind: AnalyticKind,
):
    """
    Filter catalog rows by analytical
    interpretation semantics.
    """

    return [row for row in rows if row.get("analytic_kind") == analytic_kind]


def filter_catalog_by_node_type(
    rows,
    node_type: CatalogNodeType,
):
    """
    Filter catalog rows by catalog
    graph structure semantics.
    """

    return [row for row in rows if row.get("node_type") == node_type]


# =========================================================
# Search
# =========================================================


def search_catalog(
    rows,
    query: str,
):
    """
    Simple case-insensitive catalog search.

    Searches:
        - field_name
        - path
        - description
        - owner
        - semantic_domain
        - analytic_kind
        - projection_kind
        - node_type
    """

    query = query.lower()

    results = []

    for row in rows:
        haystack = " ".join(
            str(v or "")
            for v in [
                row.get("field_name"),
                row.get("path"),
                row.get("description"),
                row.get("owner"),
                row.get("semantic_domain"),
                row.get("analytic_kind"),
                row.get("projection_kind"),
                row.get("node_type"),
            ]
        ).lower()

        if query in haystack:
            results.append(row)

    return results
