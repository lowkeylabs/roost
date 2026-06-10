# src/owlroost/display/renderers/markdown_table.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Markdown table renderer.
"""

from __future__ import annotations

from owlroost.display.formatting import (
    format_value,
)


def render_markdown_table(
    table,
):
    """
    Render RoostTable as Markdown.

    Preserves:

    - column labels
    - value formatting
    - section rows
    - blank spacer rows

    Ignores:

    - colors
    - alignment
    - widths
    - wrapping
    """

    lines: list[str] = []

    # =====================================================
    # Header
    # =====================================================

    labels = [col.label.replace("\n", " ") for col in table.columns]

    header = "| " + " | ".join(labels) + " |"

    separator = "| " + " | ".join(["---"] * len(labels)) + " |"

    lines.extend(
        [
            header,
            separator,
        ]
    )

    # =====================================================
    # Rows
    # =====================================================

    for row_idx, row in enumerate(
        table.rows,
    ):
        row_meta = None

        if hasattr(
            table,
            "row_meta",
        ):
            if row_idx < len(
                table.row_meta,
            ):
                row_meta = table.row_meta[row_idx]

        # -------------------------------------------------
        # Blank spacer rows
        # -------------------------------------------------

        if all(c is None or c == "" for c in row):
            lines.append("")
            continue

        # -------------------------------------------------
        # Structural section rows
        # -------------------------------------------------

        if (
            isinstance(
                row_meta,
                dict,
            )
            and row_meta.get("kind") == "section"
        ):
            cells = [
                f"**{row[0]}**",
            ]

            cells.extend("" for _ in table.columns[1:])

            lines.append("| " + " | ".join(cells) + " |")

            continue

        # -------------------------------------------------
        # Normal rows
        # -------------------------------------------------

        formatted = []

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

            rendered = str(
                rendered,
            ).replace(
                "\n",
                "<br>",
            )

            formatted.append(
                rendered,
            )

        lines.append("| " + " | ".join(formatted) + " |")

    return "\n".join(lines)
