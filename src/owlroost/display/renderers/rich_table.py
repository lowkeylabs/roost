# src/owlroost/display/renderers/rich_table.py

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.table import Table


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
        rich_table.add_row(*["" if c is None else str(c) for c in row])

    # =====================================================
    # Render
    # =====================================================

    console = Console()

    console.print(rich_table)

    return ""
