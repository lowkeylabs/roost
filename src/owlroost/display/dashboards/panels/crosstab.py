# src/owlroost/display/dashboards/panels/crosstab.py
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

from collections import defaultdict

from owlroost.display.dashboards.specs import (
    CrosstabPanel,
)
from owlroost.display.renderers.specs import (
    RoostTable,
    TableColumn,
)

PANEL_SPEC = CrosstabPanel


def materialize(
    panel_spec,
    *,
    rows,
    registry=None,
    catalog_index=None,
):
    """
    Materialize CrosstabPanel.

    Returns
    -------
    RoostTable
    """

    matrix = defaultdict(
        int,
    )

    for row in rows:
        row_value = row.get(
            panel_spec.row_key,
        )

        col_value = row.get(
            panel_spec.col_key,
        )

        matrix[
            (
                row_value,
                col_value,
            )
        ] += 1

    # =====================================================
    # Row/Column Ordering
    # =====================================================

    row_values = panel_spec.row_order or sorted(
        {
            row.get(
                panel_spec.row_key,
            )
            for row in rows
        }
    )

    col_values = panel_spec.col_order or sorted(
        {
            row.get(
                panel_spec.col_key,
            )
            for row in rows
        }
    )

    # =====================================================
    # Columns
    # =====================================================

    columns = [
        TableColumn(
            key=panel_spec.row_key,
            label=panel_spec.row_key,
        )
    ]

    columns.extend(
        TableColumn(
            key=str(col),
            label=str(col),
            content_align="right",
        )
        for col in col_values
    )

    # =====================================================
    # Rows
    # =====================================================

    table_rows = []

    for row_value in row_values:
        values = [
            row_value,
        ]

        for col_value in col_values:
            values.append(
                matrix[
                    (
                        row_value,
                        col_value,
                    )
                ]
            )

        table_rows.append(
            values,
        )

    return RoostTable(
        columns=columns,
        rows=table_rows,
    )
