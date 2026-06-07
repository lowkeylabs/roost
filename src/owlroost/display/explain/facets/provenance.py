# src/owlroost/display/explain/facets/provenance.py
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

FACET_NAME = "provenance"


def render(
    *,
    display_field,
    catalog_row,
    row_values,
) -> str:
    if catalog_row is None:
        return ""

    chain = catalog_row.get(
        "provenance_chain",
    ) or catalog_row.get(
        "_catalog",
        {},
    ).get(
        "provenance_chain",
        [],
    )

    if not chain:
        return ""

    lines = []

    origin_file = catalog_row.get(
        "origin_file",
    )

    defined_in = catalog_row.get(
        "defined_in",
    )

    if origin_file:
        lines.append(
            f"Origin File: {origin_file}",
        )

    if defined_in:
        lines.append(
            f"Defined In: {defined_in}",
        )

    lines.append("")

    for event in chain:
        operation = event.get(
            "operation",
        )

        if hasattr(
            operation,
            "value",
        ):
            operation = operation.value

        lines.append(
            f"{event.get('stage')}:{operation}",
        )

    return "\n".join(
        lines,
    )
