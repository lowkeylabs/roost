# src/owlroost/catalog/service.py

from __future__ import annotations

from copy import deepcopy

from owlroost.catalog.builders import (
    build_display_rows,
    build_metric_rows,
    build_schema_rows,
)

from owlroost.catalog.ontology import (
    Owner,
    ProjectionKind,
    SemanticDomain,
    ValueOrigin,
)

from owlroost.display.dataset import (
    Dataset,
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
        entities[field_name] = deepcopy(
            row
        )
        return

    existing = entities[field_name]

    # =====================================================
    # Layer Validation
    # =====================================================

    existing_layer = existing.get(
        "layer"
    )

    incoming_layer = row.get(
        "layer"
    )

    # -----------------------------------------------------
    # Canonical ontology collisions are illegal
    # -----------------------------------------------------

    if (
        existing_layer
        in {
            "schema",
            "metrics",
        }
        and incoming_layer
        in {
            "schema",
            "metrics",
        }
    ):
        raise ValueError(
            "Duplicate canonical semantic "
            f"identity detected: "
            f"{field_name}"
        )

    # =====================================================
    # Display Overlay Merge
    # =====================================================

    if incoming_layer == "display":

        # -------------------------------------------------
        # Overlay non-null metadata only
        # -------------------------------------------------

        for key, value in row.items():

            if value is None:
                continue

            # Preserve canonical ontology
            if key in {
                "layer",
                "field_name",
            }:
                continue

            existing[key] = value

        # -------------------------------------------------
        # Track overlay provenance
        # -------------------------------------------------

        overlays = existing.setdefault(
            "_overlay_layers",
            [],
        )

        overlays.append(
            "display"
        )

        return

    # =====================================================
    # Unknown merge behavior
    # =====================================================

    raise ValueError(
        "Unsupported catalog merge: "
        f"{field_name} "
        f"({existing_layer} <- "
        f"{incoming_layer})"
    )


# =========================================================
# Catalog Loader
# =========================================================


def load_catalog(
    *,
    schema_registry,
    metrics_registry,
    display_registry,
):
    """
    Build unified semantic catalog dataset.

    Notes
    -----
    The catalog subsystem acts as semantic
    integration infrastructure layered across:

        - schema ontology
        - metrics ontology
        - display overlays
        - aggregation synthesis

    The catalog intentionally models:

        canonical semantic entities

    rather than flattened registry rows.

    Architectural Invariant
    -----------------------
    Exactly one catalog row exists for each:

        field_name
    """

    # =====================================================
    # Canonical Semantic Entity Map
    # =====================================================

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
    # Display Overlays
    # =====================================================

    for row in build_display_rows(
        display_registry,
    ):
        _merge_row(
            entities,
            row,
        )

    # =====================================================
    # Stable Ordering
    # =====================================================

    rows = sorted(
        entities.values(),
        key=lambda r: (
            r.get("owner") or "",
            r.get(
                "semantic_domain"
            )
            or "",
            r.get(
                "projection_kind"
            )
            or "",
            r.get("field_name")
            or "",
        ),
    )

    # =====================================================
    # Dataset
    # =====================================================

    return Dataset(
        rows,
        level="catalog",
    )


# =========================================================
# Ontology Filters
# =========================================================


def filter_catalog_by_layer(
    dataset,
    layer: str,
):
    """
    Filter catalog dataset by ontology layer.
    """

    rows = [
        row
        for row in dataset.rows
        if row.get("layer")
        == layer
    ]

    return Dataset(
        rows,
        level=dataset.level,
    )


def filter_catalog_by_owner(
    dataset,
    owner: Owner,
):
    """
    Filter catalog dataset by ontology owner.
    """

    rows = [
        row
        for row in dataset.rows
        if row.get("owner")
        == owner
    ]

    return Dataset(
        rows,
        level=dataset.level,
    )


def filter_catalog_by_semantic_domain(
    dataset,
    semantic_domain: SemanticDomain,
):
    """
    Filter catalog dataset by semantic domain.
    """

    rows = [
        row
        for row in dataset.rows
        if row.get(
            "semantic_domain"
        )
        == semantic_domain
    ]

    return Dataset(
        rows,
        level=dataset.level,
    )


def filter_catalog_by_value_origin(
    dataset,
    value_origin: ValueOrigin,
):
    """
    Filter catalog dataset by value origin.
    """

    rows = [
        row
        for row in dataset.rows
        if row.get("value_origin")
        == value_origin
    ]

    return Dataset(
        rows,
        level=dataset.level,
    )


def filter_catalog_by_projection_kind(
    dataset,
    projection_kind: ProjectionKind,
):
    """
    Filter catalog dataset by analytical
    projection realization.
    """

    rows = [
        row
        for row in dataset.rows
        if row.get(
            "projection_kind"
        )
        == projection_kind
    ]

    return Dataset(
        rows,
        level=dataset.level,
    )


# =========================================================
# Search
# =========================================================


def search_catalog(
    dataset,
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
        - projection_kind
    """

    query = query.lower()

    rows = []

    for row in dataset.rows:

        haystack = " ".join(
            str(v or "")
            for v in [
                row.get("field_name"),
                row.get("path"),
                row.get("description"),
                row.get("owner"),
                row.get(
                    "semantic_domain"
                ),
                row.get(
                    "projection_kind"
                ),
            ]
        ).lower()

        if query in haystack:
            rows.append(row)

    return Dataset(
        rows,
        level=dataset.level,
    )
