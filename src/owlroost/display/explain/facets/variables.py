# src/owlroost/display/explain/facets/variables.py
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

FACET_NAME = "variables"


def render(
    *,
    display_field,
    catalog_row,
    row_values,
) -> str:
    return (
        (catalog_row or {}).get(
            "description",
            "",
        )
        or getattr(
            display_field,
            "description",
            "",
        )
        or ""
    )
