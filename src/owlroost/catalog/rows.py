# src/owlroost/catalog/rows.py

from __future__ import annotations


def build_catalog_row(
    *,
    field_name: str,
    layer: str,
    source: str,
    path: str | None = None,
    description: str | None = None,
    semantic_owner: str | None = None,
    semantic_field=None,
    display_field=None,
):
    """
    Construct canonical catalog dataset row.

    Notes
    -----
    This intentionally mirrors the existing dataset-style
    row structure used elsewhere in ROOST.

    The catalog subsystem is designed to integrate with:

        - filtering
        - sorting
        - materialization
        - renderers
        - explainability
        - provenance tracing

    without introducing a second table architecture.
    """

    return {
        "_meta": {
            "layer": layer,
        },
        "_catalog": {
            "field_name": field_name,
            "source": source,
            "path": path,
            "semantic_owner": semantic_owner,
        },
        "_display": {
            "description": description,
        },
        "_objects": {
            "semantic_field": semantic_field,
            "display_field": display_field,
        },
        # -------------------------------------------------
        # Flattened convenience aliases
        #
        # These make filtering/rendering easier.
        # -------------------------------------------------
        "field_name": field_name,
        "layer": layer,
        "source": source,
        "path": path,
        "description": description,
        "semantic_owner": semantic_owner,
    }
