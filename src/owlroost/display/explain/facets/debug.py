# src/owlroost/display/explain/facets/debug.py
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

from pprint import pformat

FACET_NAME = "debug"


def render(
    *,
    display_field,
    catalog_row,
    row_values,
) -> str:
    return pformat(
        {
            "catalog_row": catalog_row,
            "display_field": (
                vars(
                    display_field,
                )
                if display_field
                else None
            ),
        },
        width=100,
        sort_dicts=False,
    )
