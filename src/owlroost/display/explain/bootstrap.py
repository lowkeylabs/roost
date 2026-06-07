# src/owlroost/display/explain/bootstrap.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
Display explanation rendering.

Notes
-----
Owns explanation construction for
pivot-table explain columns.

Architectural Invariant
-----------------------

Explanation rendering consumes
already-materialized metadata from:

    - CatalogSpec
    - DisplayField

Facet rendering is delegated to
auto-discovered facet plugins located in:

    display.explain.facets
"""

from __future__ import annotations

from owlroost.display.explain.facets import (
    FACETS,
)

# =========================================================
# Helpers
# =========================================================


def _render_parts(
    parts: list[str],
) -> str:
    parts = [part for part in parts if part]

    return "\n\n".join(
        parts,
    )


# =========================================================
# Field Explanation
# =========================================================


def build_field_explanation(
    *,
    display_field,
    catalog_row=None,
    explain_facets: set[str],
    row_values=None,
) -> str:
    """
    Build explanation text.
    """

    if not explain_facets:
        return ""

    parts = []

    for facet_name in sorted(
        explain_facets,
    ):
        render_fn = FACETS.get(
            facet_name,
        )

        if render_fn is None:
            continue

        try:
            text = render_fn(
                display_field=display_field,
                catalog_row=catalog_row,
                row_values=row_values,
            )

        except Exception as ex:
            text = f"[facet error: {facet_name}: {type(ex).__name__}: {ex}]"

        if text:
            parts.append(
                text,
            )

    return _render_parts(
        parts,
    )


# =========================================================
# Cell Builder
# =========================================================


def build_explanation_cell(
    *,
    field_name: str,
    registry=None,
    catalog_index=None,
    explain_facets: set[str] | None = None,
    row_values=None,
) -> str:
    """
    Build explanation cell.

    Materializers should call this
    function rather than interacting
    with facets directly.
    """

    if not explain_facets:
        return ""

    try:
        display_field = None

        if registry is not None:
            try:
                display_field = registry.get_display_field(
                    field_name,
                )
            except KeyError:
                pass

        catalog_row = None

        if catalog_index is not None:
            catalog_row = catalog_index.get(
                field_name,
            )

        return build_field_explanation(
            display_field=display_field,
            catalog_row=catalog_row,
            explain_facets=explain_facets,
            row_values=row_values,
        )

    except Exception as ex:
        return f"explain error: {type(ex).__name__}: {ex}"
