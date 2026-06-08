# src/owlroost/display/explain/facets/ontology.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

FACET_NAME = "ontology"


def render(
    *,
    display_field,
    catalog_row,
    row_values,
) -> str:
    if catalog_row is None:
        return ""

    lines = [
        f"Owner: {catalog_row.get('owner')}",
        f"Domain: {catalog_row.get('semantic_domain')}",
        f"Origin: {catalog_row.get('value_origin')}",
        f"Projection: {catalog_row.get('projection_kind')}",
        f"Analytic: {catalog_row.get('analytic_kind')}",
        f"Level: {catalog_row.get('materialization_level')}",
        f"Type: {catalog_row.get('node_type')}",
    ]

    derived_from = (
        catalog_row.get(
            "derived_from",
            [],
        )
        or []
    )

    materializes_to = (
        catalog_row.get(
            "materializes_to",
            [],
        )
        or []
    )

    if derived_from:
        lines.append(
            "Derived From: "
            + ", ".join(
                derived_from,
            )
        )

    if materializes_to:
        lines.append(
            "Expands To: "
            + ", ".join(
                materializes_to,
            )
        )

    return "\n".join(
        lines,
    )
