# src/owlroost/display/explain/facets/sources.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

FACET_NAME = "sources"


def render(
    *,
    display_field,
    catalog_row,
    row_values,
) -> str:
    if catalog_row is None:
        return ""

    source = catalog_row.get(
        "source",
    )

    origin = catalog_row.get(
        "value_origin",
    )

    return f"{origin} / {source}"
