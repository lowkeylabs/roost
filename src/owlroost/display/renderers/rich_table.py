# src/owlroost/display/renderers/rich_table.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

import textwrap

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
        - structural compare tables

    Pivot/compare tables preserve formatting metadata
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
        row_meta = None

        if hasattr(
            table,
            "row_meta",
        ):
            if row_idx < len(table.row_meta):
                row_meta = table.row_meta[row_idx]

        # -------------------------------------------------
        # Blank spacer rows
        # -------------------------------------------------

        if all((c is None or c == "") for c in row):
            rich_table.add_row(*["" for _ in row])
            continue

        # -------------------------------------------------
        # Structural section rows
        # -------------------------------------------------

        if isinstance(row_meta, dict) and row_meta.get("kind") == "section":
            rich_table.add_row(*["" for _ in table.columns])

            cells = [row[0]]

            cells.extend(["" for _ in table.columns[1:]])

            rich_table.add_row(
                *cells,
                style="bold cyan",
            )

            continue

        formatted = []

        # -------------------------------------------------
        # Row style
        # -------------------------------------------------

        row_style = None

        if isinstance(
            row_meta,
            dict,
        ):
            if row_meta.get("dim"):
                row_style = "dim"

        # -------------------------------------------------
        # Row-level formatting metadata
        #
        # Pivot tables store the originating
        # display column in row_meta["column"].
        #
        # This allows rows such as:
        #
        #     Description
        #     Provenance Chain
        #
        # to inherit width/wrap behavior from
        # their original display definition.
        # -------------------------------------------------

        row_wrap = False
        row_width = None

        if isinstance(
            row_meta,
            dict,
        ):
            meta_column = row_meta.get(
                "column",
            )

            if meta_column is not None:
                row_wrap = bool(
                    getattr(
                        meta_column,
                        "wrap",
                        False,
                    )
                )

                row_width = getattr(
                    meta_column,
                    "width",
                    None,
                )

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
            fmt = column.fmt

            # -----------------------------------------
            # Pivot formatting metadata
            # -----------------------------------------

            if row_meta is not None and col_idx > 0:
                if isinstance(
                    row_meta,
                    dict,
                ):
                    meta_column = row_meta.get(
                        "column",
                    )

                    if meta_column is not None:
                        fmt = meta_column.fmt

                else:
                    fmt = row_meta.fmt

            rendered = format_value(
                value,
                fmt,
            )

            # -----------------------------------------
            # Row-aware wrapping
            #
            # Rich widths belong to columns,
            # not rows. Pivot tables invert
            # this relationship.
            #
            # Therefore manually wrap values
            # using the originating field's
            # configured width.
            # -----------------------------------------

            if (
                col_idx > 0
                and row_wrap
                and row_width
                and isinstance(
                    rendered,
                    str,
                )
                and rendered
            ):
                rendered = "\n".join(
                    textwrap.wrap(
                        rendered,
                        width=row_width,
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                )

            formatted.append(
                rendered,
            )

        rich_table.add_row(
            *formatted,
            style=row_style,
        )

    # =====================================================
    # Render
    # =====================================================

    console = Console()

    console.print(
        rich_table,
    )

    return ""
