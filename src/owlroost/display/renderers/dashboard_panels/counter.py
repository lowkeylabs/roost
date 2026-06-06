# src/owlroost/display/renderers/dashboard_panels/counter.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from rich.table import Table


def render_rich_counter(
    panel,
):
    """
    Render counter panel.
    """

    table = Table(
        expand=True,
        show_header=True,
        box=None,
        show_edge=False,
    )

    table.add_column(
        "Value",
    )

    table.add_column(
        "Count",
        justify="right",
    )

    for value, count in panel.content:
        table.add_row(
            str(value),
            str(count),
        )

    return table
