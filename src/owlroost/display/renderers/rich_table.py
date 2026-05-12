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
        )

    # =====================================================
    # Rows
    # =====================================================

    for row in table.rows:
        formatted = []

        for value, column in zip(
            row,
            table.columns,
            strict=False,
        ):
            formatted.append(
                format_value(
                    value,
                    column.fmt,
                )
            )

        rich_table.add_row(*formatted)

    # =====================================================
    # Render
    # =====================================================

    console = Console()

    console.print(rich_table)

    return ""
