# src/owlroost/display/renderers/dashboard_panels/crosstab.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from rich.table import Table


def render_rich_crosstab(
    panel,
):
    """
    Render crosstab panel.
    """

    matrix = panel.content["matrix"]

    row_order = (
        panel.content.get(
            "row_order",
        )
        or []
    )

    col_order = (
        panel.content.get(
            "col_order",
        )
        or []
    )

    table = Table(
        expand=True,
        show_header=True,
        box=None,
        show_edge=False,
    )

    table.add_column("")

    for col in col_order:
        table.add_column(
            str(col),
            justify="right",
        )

    for row in row_order:
        values = []

        for col in col_order:
            values.append(
                str(
                    matrix.get(
                        (row, col),
                        0,
                    )
                )
            )

        table.add_row(
            str(row),
            *values,
        )

    return table
