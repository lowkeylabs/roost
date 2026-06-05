# src/owlroost/display/explain/facets/ontology.py

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

    expands_to = (
        catalog_row.get(
            "expands_to",
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

    if expands_to:
        lines.append(
            "Expands To: "
            + ", ".join(
                expands_to,
            )
        )

    return "\n".join(
        lines,
    )
