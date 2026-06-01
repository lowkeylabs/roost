# src/owlroost/catalog/loaders.py

"""
Catalog loader services.

Provides filtered and searchable access
to the canonical semantic catalog.

Notes
-----
The catalog subsystem owns semantic
identity and ontology.

Catalog returns semantic rows and does
not return renderer-facing structures.
"""

from __future__ import annotations

from owlroost.catalog.ontology import (
    CatalogNodeType,
    Owner,
    ProjectionKind,
    SemanticDomain,
    ValueOrigin,
)
from owlroost.catalog.service import (
    filter_catalog_by_layer,
    load_catalog,
    search_catalog,
)

# =========================================================
# Public Loader
# =========================================================


def load_catalog_rows(
    *,
    schema_registry,
    metrics_registry,
    # -----------------------------------------------------
    # Ontology Filters
    # -----------------------------------------------------
    layer: str | None = None,
    owner: Owner | None = None,
    semantic_domain: SemanticDomain | None = None,
    value_origin: ValueOrigin | None = None,
    projection_kind: ProjectionKind | None = None,
    node_type: CatalogNodeType | None = None,
    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------
    search: str | None = None,
):
    """
    Load filtered catalog rows.

    Notes
    -----
    Catalog synthesis integrates:

        - schema ontology
        - metrics ontology

    into a unified semantic entity graph.

    Display consumes catalog semantics
    downstream.

    Architectural Invariant
    -----------------------
    Catalog owns semantic identity.

    Display owns presentation identity.

    Catalog therefore returns semantic
    rows rather than renderer-facing
    structures such as:

        - RoostTable
        - TableColumn
    """

    # =====================================================
    # Canonical Catalog
    # =====================================================

    rows = load_catalog(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
    )

    # =====================================================
    # Layer Filter
    # =====================================================

    if layer:
        rows = filter_catalog_by_layer(
            rows,
            layer,
        )

    # =====================================================
    # Ontology Filters
    # =====================================================

    def matches(
        row,
    ) -> bool:
        if owner is not None and row.get("owner") != owner:
            return False

        if semantic_domain is not None and row.get("semantic_domain") != semantic_domain:
            return False

        if value_origin is not None and row.get("value_origin") != value_origin:
            return False

        if projection_kind is not None and row.get("projection_kind") != projection_kind:
            return False

        if node_type is not None and row.get("node_type") != node_type:
            return False

        return True

    rows = [row for row in rows if matches(row)]

    # =====================================================
    # Search Filter
    # =====================================================

    if search:
        rows = search_catalog(
            rows,
            search,
        )

    # =====================================================
    # Final Rows
    # =====================================================

    return rows
