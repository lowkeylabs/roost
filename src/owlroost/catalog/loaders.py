# src/owlroost/catalog/loaders.py

from __future__ import annotations

from owlroost.catalog.service import (
    filter_catalog_by_layer,
    load_catalog,
    search_catalog,
)

# =========================================================
# Public Loader
# =========================================================


def load_catalog_dataset(
    *,
    schema_registry,
    metrics_registry,
    display_registry,
    layer: str | None = None,
    search: str | None = None,
):
    """
    Load catalog dataset with optional filtering.

    Parameters
    ----------
    layer
        Optional ontology layer filter.

        Examples:
            schema
            metrics
            display

    search
        Optional case-insensitive substring search.
    """

    dataset = load_catalog(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
        display_registry=display_registry,
    )

    # =====================================================
    # Layer filter
    # =====================================================

    if layer:
        dataset = filter_catalog_by_layer(
            dataset,
            layer,
        )

    # =====================================================
    # Search filter
    # =====================================================

    if search:
        dataset = search_catalog(
            dataset,
            search,
        )

    return dataset
