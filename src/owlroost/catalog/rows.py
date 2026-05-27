# src/owlroost/catalog/rows.py

from __future__ import annotations

from dataclasses import (
    asdict,
    is_dataclass,
)

from owlroost.catalog.specs import (
    CatalogSpec,
    ProvenanceEvent,
)

# =========================================================
# Safe Export Helpers
# =========================================================


def _safe_export(
    obj,
):
    """
    Safely export lightweight renderer-friendly
    metadata representations.

    Notes
    -----
    Catalog rows intentionally avoid storing
    large runtime object graphs directly.

    Exported objects should remain:

        - serializable
        - renderer-safe
        - debugging-friendly
        - stable across CLI/renderers
    """

    if obj is None:
        return None

    if is_dataclass(obj):
        return asdict(obj)

    # -----------------------------------------------------
    # Avoid leaking large object graphs
    # -----------------------------------------------------

    return {
        "type": type(obj).__name__,
    }


def _export_provenance_chain(
    chain: list[ProvenanceEvent],
):
    """
    Export provenance chain into stable,
    renderer-safe structures.
    """

    rows = []

    for event in chain:

        if is_dataclass(event):
            rows.append(
                asdict(event)
            )

        else:
            rows.append(
                {
                    "type": str(
                        type(event).__name__
                    )
                }
            )

    return rows


# =========================================================
# Catalog Row Builder
# =========================================================


def build_catalog_row(
    *,
    spec: CatalogSpec,
    layer: str,
    semantic_field=None,
    display_field=None,
):
    """
    Construct canonical catalog dataset row.

    Notes
    -----
    Catalog rows intentionally model:

        semantic entities

    rather than merely registry emissions.

    Rows are shaped for natural integration
    with:

        - filtering
        - sorting
        - rendering
        - explainability
        - provenance tracing
        - CLI workflows
        - reporting systems

    while preserving ontology semantics.
    """

    # =====================================================
    # Provenance
    # =====================================================

    provenance_chain = (
        _export_provenance_chain(
            spec.provenance_chain
        )
    )

    # =====================================================
    # Overlay Metadata
    # =====================================================

    overlay_layers: list[str] = []

    if layer == "display":
        overlay_layers.append(
            "display"
        )

    # =====================================================
    # Canonical Row
    # =====================================================

    row = {
        # -------------------------------------------------
        # Operational Metadata
        # -------------------------------------------------
        "_meta": {
            "layer": layer,
        },
        # -------------------------------------------------
        # Canonical Ontology
        # -------------------------------------------------
        "_catalog": {
            "field_name": spec.field_name,
            "owner": spec.owner,
            "semantic_domain": (
                spec.semantic_domain
            ),
            "value_origin": (
                spec.value_origin
            ),
            "projection_kind": (
                spec.projection_kind
            ),
            "materialization_level": (
                spec.materialization_level
            ),
            "source": spec.source,
            "path": spec.path,
            "derived_from": (
                spec.derived_from
            ),
            "provenance_chain": (
                provenance_chain
            ),
            "overlay_layers": (
                overlay_layers
            ),
        },
        # -------------------------------------------------
        # Explainability / Presentation
        # -------------------------------------------------
        "_display": {
            "description": (
                spec.description
            ),
        },
        # -------------------------------------------------
        # Lightweight Registry References
        # -------------------------------------------------
        "_objects": {
            "semantic_field": (
                _safe_export(
                    semantic_field
                )
            ),
            "display_field": (
                _safe_export(
                    display_field
                )
            ),
        },
        # -------------------------------------------------
        # Flattened Convenience Aliases
        #
        # These simplify:
        #   - filtering
        #   - sorting
        #   - rendering
        #   - CLI workflows
        # -------------------------------------------------
        "field_name": spec.field_name,
        "layer": layer,
        "owner": spec.owner,
        "semantic_domain": (
            spec.semantic_domain
        ),
        "value_origin": (
            spec.value_origin
        ),
        "projection_kind": (
            spec.projection_kind
        ),
        "materialization_level": (
            spec.materialization_level
        ),
        "source": spec.source,
        "path": spec.path,
        "description": (
            spec.description
        ),
        "derived_from": (
            ", ".join(
                spec.derived_from
            )
            if spec.derived_from
            else ""
        ),
        "provenance_depth": len(
            provenance_chain
        ),
        "overlay_layers": (
            ", ".join(
                overlay_layers
            )
            if overlay_layers
            else ""
        ),
    }

    return row
