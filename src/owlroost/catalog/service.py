# src/owlroost/catalog/service.py

from __future__ import annotations

from owlroost.display.dataset import Dataset

from .builders import (
    build_display_rows,
    build_metric_rows,
    build_schema_rows,
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
    Build unified catalog dataset.

    The catalog intentionally operates as a
    lightweight introspection and provenance
    layer over the existing ontology systems.

    Current ontology layers:

        schema   -> executable ontology
        metrics  -> observable ontology
        display  -> analytical projection ontology

    The catalog normalizes these into
    dataset-style rows suitable for:

        - filtering
        - sorting
        - rendering
        - explainability
        - provenance tracing
    """

    rows = []

    # =====================================================
    # Schema ontology
    # =====================================================

    rows.extend(
        build_schema_rows(
            schema_registry,
        )
    )

    # =====================================================
    # Observable ontology
    # =====================================================

    rows.extend(
        build_metric_rows(
            metrics_registry,
        )
    )

    # =====================================================
    # Analytical projection ontology
    # =====================================================

    rows.extend(
        build_display_rows(
            display_registry,
        )
    )

    # =====================================================
    # Stable ordering
    # =====================================================

    rows = sorted(
        rows,
        key=lambda r: (
            r["layer"],
            r["field_name"],
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
# Helpers
# =========================================================


def filter_catalog_by_layer(
    dataset,
    layer: str,
):
    """
    Filter catalog dataset by ontology layer.
    """

    rows = [row for row in dataset.rows if row.get("layer") == layer]

    return Dataset(
        rows,
        level=dataset.level,
    )


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
            ]
        ).lower()

        if query in haystack:
            rows.append(row)

    return Dataset(
        rows,
        level=dataset.level,
    )
