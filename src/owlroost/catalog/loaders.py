# src/owlroost/catalog/loaders.py

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
# Helpers
# =========================================================


def _rebuild_dataset(
    dataset,
    rows,
):
    """
    Rebuild dataset preserving dataset type
    and semantic level metadata.
    """

    return type(dataset)(
        rows=list(rows),
        level=dataset.level,
    )


# =========================================================
# Public Loader
# =========================================================


def load_catalog_dataset(
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
    Load ontology-centered catalog dataset.

    Notes
    -----
    The catalog subsystem models:

        canonical semantic entities

    rather than display overlays,
    registry rows, or renderer-facing
    structures.

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

    Catalog therefore returns:

        Dataset(level="catalog")

    rather than renderer-facing
    objects such as:

        - RoostTable
        - TableColumn

    Parameters
    ----------
    layer
        Optional ontology layer filter.

        Examples:

            schema
            metrics

    owner
        Semantic ownership filter.

        Examples:

            OWL
            ROOST

    semantic_domain
        Scientific workflow role filter.

        Examples:

            decision
            design
            execution

    value_origin
        Fundamental value provenance filter.

        Examples:

            user-specified
            owl-computed
            roost-computed

    projection_kind
        Analytical realization filter.

    node_type
        Optional catalog graph filter.

    search
        Optional case-insensitive substring
        search across catalog semantics.
    """

    # =====================================================
    # Canonical Catalog Dataset
    # =====================================================

    dataset = load_catalog(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
    )

    # =====================================================
    # Layer Filter
    # =====================================================

    if layer:

        dataset = filter_catalog_by_layer(
            dataset,
            layer,
        )

    # =====================================================
    # Ontology Filters
    # =====================================================

    def matches(
        row,
    ) -> bool:

        if (
            owner is not None
            and row.get("owner") != owner
        ):
            return False

        if (
            semantic_domain is not None
            and row.get("semantic_domain")
            != semantic_domain
        ):
            return False

        if (
            value_origin is not None
            and row.get("value_origin")
            != value_origin
        ):
            return False

        if (
            projection_kind is not None
            and row.get("projection_kind")
            != projection_kind
        ):
            return False

        if (
            node_type is not None
            and row.get("node_type")
            != node_type
        ):
            return False

        return True

    rows = [
        row
        for row in dataset.rows
        if matches(row)
    ]

    dataset = _rebuild_dataset(
        dataset,
        rows,
    )

    # =====================================================
    # Search Filter
    # =====================================================

    if search:

        dataset = search_catalog(
            dataset,
            search,
        )

    # =====================================================
    # Final Dataset
    # =====================================================

    return dataset
