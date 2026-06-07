# src/owlroost/display/explain/facets/values.py
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

FACET_NAME = "values"


def render(
    *,
    display_field,
    catalog_row,
    row_values,
) -> str:
    if display_field is None:
        return ""

    def clip(
        text: str,
        width: int = 22,
    ) -> str:
        if len(text) <= width:
            return text

        return text[: width - 3] + "..."

    values = [clip(str(value)) for value in (row_values or [])]

    return f"{display_field.field_name}: ['" + "','".join(values) + "']"
