# src/owlroost/display/views/catalog.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Catalog display views.

Notes
-----
Catalog inspection and semantic
introspection views.
"""

from __future__ import annotations

from owlroost.display.specs import (
    DisplayView,
)


def register_display_views(
    reg,
):
    """
    Register catalog inspection views.
    """

    reg.register_view(
        DisplayView(
            level="catalog",
            name="summary",
            entries=[
                # =====================================
                # Identity
                # =====================================
                ("section", "Identity"),
                "field_name",
                "owner",
                # =====================================
                # Catalog
                # =====================================
                ("section", "Catalog"),
                ("path", {"modes": ["pivot"]}),
                ("layer", {"modes": ["pivot"]}),
                ("source", {"modes": ["pivot"]}),
                ("overlay_layers", {"modes": ["pivot"]}),
                # =====================================
                # Ontology
                # =====================================
                ("section", "Ontology"),
                ("semantic_domain", {"modes": ["pivot"]}),
                ("value_origin", {"modes": ["pivot"]}),
                ("projection_kind", {"modes": ["pivot"]}),
                ("analytic_kind", {"modes": ["pivot"]}),
                ("materialization_level", {"modes": ["pivot"]}),
                ("node_type", {"modes": ["pivot"]}),
                # =====================================
                # Relationships
                # =====================================
                ("section", "Relationships"),
                ("derived_from", {"modes": ["pivot"]}),
                # ("materializes_to", {"modes": ["pivot"]}),  # not for this view!
                # =====================================
                # Provenance
                # =====================================
                ("section", "Provenance"),
                ("origin_file", {"modes": ["pivot"]}),
                ("defined_in", {"modes": ["pivot"]}),
                ("provenance_depth", {"modes": ["pivot"]}),
                ("provenance_chain", {"modes": ["pivot"]}),
                # =====================================
                # Display
                # =====================================
                ("section", "Display"),
                ("display_name", {"modes": ["pivot"]}),
                ("profiles", {"modes": ["pivot"]}),
                # Future:
                #
                # ("used_by_groups", {"modes": ["pivot"]}),
                # ("used_by_views", {"modes": ["pivot"]}),
                # =====================================
                # Documentation
                # =====================================
                ("section", "Documentation"),
                ("description", {"modes": ["pivot"]}),
            ],
            description=(
                "Canonical catalog inspection view. "
                "Table mode supports catalog browsing "
                "and selection. Pivot mode exposes "
                "catalog identity, ontology, semantic "
                "relationships, provenance, display "
                "metadata, and documentation."
            ),
        )
    )
