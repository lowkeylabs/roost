# src/owlroost/display/renderers/rich_table.py

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.table import Table

from owlroost.display.formatting import (
    format_value,
)


def render_rich_table(
    table,
):
    """
    Render RoostTable using Rich.

    Supports:
        - normal tables
        - pivot tables

    Pivot tables preserve formatting metadata
    using table.row_meta.
    """

    rich_table = Table(
        box=box.HORIZONTALS,
        show_edge=False,
        show_lines=False,
    )

    # =====================================================
    # Columns
    # =====================================================

    for col in table.columns:
        if col.content_align == "right":
            justify = "right"

        elif col.content_align == "center":
            justify = "center"

        else:
            justify = "left"

        rich_table.add_column(
            col.label,
            justify=justify,
            width=col.width,
            no_wrap=not col.wrap,
        )

    # =====================================================
    # Rows
    # =====================================================

    for row_idx, row in enumerate(table.rows):
        formatted = []

        # -------------------------------------------------
        # Optional row metadata (pivot support)
        # -------------------------------------------------

        row_meta = None

        if hasattr(
            table,
            "row_meta",
        ):
            if row_idx < len(table.row_meta):
                row_meta = table.row_meta[row_idx]

        # -------------------------------------------------
        # Cells
        # -------------------------------------------------

        for col_idx, (
            value,
            column,
        ) in enumerate(
            zip(
                row,
                table.columns,
                strict=False,
            )
        ):
            # ---------------------------------------------
            # Default column formatting
            # ---------------------------------------------

            fmt = column.fmt

            # ---------------------------------------------
            # Pivot formatting
            #
            # In pivot tables:
            #   - column 0 is metric label
            #   - remaining cells inherit formatting
            #     from original source column
            # ---------------------------------------------

            if row_meta is not None and col_idx > 0:
                fmt = row_meta.fmt

            formatted.append(
                format_value(
                    value,
                    fmt,
                )
            )

        rich_table.add_row(*formatted)

    # =====================================================
    # Render
    # =====================================================

    console = Console()

    console.print(rich_table)

    return ""
