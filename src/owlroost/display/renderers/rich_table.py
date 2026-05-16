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
            overflow="fold",
            vertical="top",
        )

    # =====================================================
    # Rows
    # =====================================================

    for row_idx, row in enumerate(table.rows):
        # -------------------------------------------------
        # Blank spacer rows
        # -------------------------------------------------

        if all((c is None or c == "") for c in row):
            rich_table.add_row(*["" for _ in row])

            continue

        # -------------------------------------------------
        # Compare section headers
        # -------------------------------------------------

        if (
            len(row) > 0
            and isinstance(row[0], str)
            and row[0].startswith("[")
            and row[0].endswith("]")
        ):
            rich_table.add_row(
                row[0],
                *["" for _ in row[1:]],
                style="bold cyan",
            )

            continue

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
            # ---------------------------------------------

            if row_meta is not None and col_idx > 0:
                # -------------------------------------------------
                # New structured row_meta support
                # -------------------------------------------------

                if isinstance(row_meta, dict):
                    meta_column = row_meta.get("column")

                    if meta_column is not None:
                        fmt = meta_column.fmt

                # -------------------------------------------------
                # Backward compatibility
                # -------------------------------------------------

                else:
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
