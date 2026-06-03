# src/owlroost/display/views/catalog.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.display.specs import (
    DisplayView,
)


def register_display_views(
    reg,
):
    """
    Register all display views.

    Views are declarative layouts composed
    from reusable display groups and fields.

    Views are uniquely identified by:

        (level, name)

    Examples:

        ("case", "basic")
        ("run", "results")
        ("session", "results")
    """

    reg.register_view(
        DisplayView(
            level="catalog",
            name="summary",
            entries=[
                # =====================================
                # Identity
                # =====================================
                "field_name",
                "owner",
                # =====================================
                # Catalog
                # =====================================
                ("path", {"modes": ["pivot"]}),
                ("layer", {"modes": ["pivot"]}),
                ("source", {"modes": ["pivot"]}),
                ("overlay_layers", {"modes": ["pivot"]}),
                # =====================================
                # Ontology
                # =====================================
                ("semantic_domain", {"modes": ["pivot"]}),
                ("value_origin", {"modes": ["pivot"]}),
                ("projection_kind", {"modes": ["pivot"]}),
                ("analytic_kind", {"modes": ["pivot"]}),
                ("materialization_level", {"modes": ["pivot"]}),
                ("node_type", {"modes": ["pivot"]}),
                # =====================================
                # Provenance
                # =====================================
                ("derived_from", {"modes": ["pivot"]}),
                ("origin_file", {"modes": ["pivot"]}),
                ("defined_in", {"modes": ["pivot"]}),
                ("provenance_depth", {"modes": ["pivot"]}),
                ("provenance_chain", {"modes": ["pivot"]}),
                # =====================================
                # Display
                # =====================================
                ("display_name", {"modes": ["pivot"]}),
                ("profiles", {"modes": ["pivot"]}),
                # =====================================
                # Documentation
                # =====================================
                ("description", {"modes": ["pivot"]}),
            ],
            description=(
                "Canonical catalog inspection view. "
                "Table mode supports catalog browsing "
                "and selection. Pivot mode exposes "
                "complete catalog identity, ontology, "
                "provenance, display metadata, and "
                "documentation."
            ),
        )
    )
