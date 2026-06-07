# src/owlroost/display/operations/table_ops.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Table operations.

Notes
-----
Utilities operating on materialized
RoostTable instances.
"""

from __future__ import annotations

from owlroost.display.renderers.specs import (
    TableColumn,
)

# =========================================================
# Table Utilities
# =========================================================


def inject_id_column(
    table,
    rows,
):
    """
    Inject row IDs into a materialized table.

    Assumes rows already contain:

        _row_id

    as attached by attach_row_ids().
    """

    table.columns = [
        TableColumn(
            key="_row_id",
            label="ID",
            label_align="right",
            content_align="right",
        )
    ] + list(
        table.columns,
    )

    table.rows = [
        [str(row["_row_id"])] + list(table_row)
        for table_row, row in zip(
            table.rows,
            rows,
            strict=False,
        )
    ]

    return table
