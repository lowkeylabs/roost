# src/owlroost/display/materializers/compare.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from pathlib import Path

from owlroost.catalog.comparison import (
    build_compare_entries,
    format_compare_value,
)
from owlroost.display.explain import (
    build_explanation_cell,
)
from owlroost.display.operations.profiles import (
    resolve_display_profile,
)
from owlroost.display.registry import DisplayRegistry
from owlroost.display.renderers.specs import (
    RoostTable,
    TableColumn,
)

# =========================================================
# Table Materialization
# =========================================================


def materialize_compare_table(
    rows,
    *,
    diff_only=False,
    registry: DisplayRegistry | None = None,
    catalog_index=None,
    explain_facets=None,
):
    """
    Materialize structural compare/diff table.

    Returns RoostTable.
    """

    explain_facets = explain_facets or set()

    explain_enabled = bool(
        explain_facets,
    )

    entries = build_compare_entries(
        rows,
        diff_only=diff_only,
    )

    # =====================================================
    # Columns
    # =====================================================

    columns = [
        TableColumn(
            key="field",
            label="Field",
            content_align="left",
        )
    ]

    for i, row in enumerate(rows):
        label = None

        paths = row.get(
            "_paths",
            {},
        )

        case_file = paths.get(
            "case_file",
        )

        if case_file:
            label = Path(case_file).name
        else:
            label = f"{i}"

        columns.append(
            TableColumn(
                key=f"col_{i}",
                label=label,
                content_align="left",
            )
        )

    # =====================================================
    # Optional Explanation Column
    # =====================================================

    explanation_profile = None

    if registry is not None:
        try:
            explanation_profile = resolve_display_profile(
                registry.get_display_field(
                    "pivot_explanation",
                ),
                mode="pivot",
            )
        except KeyError:
            pass

    if explain_enabled:
        columns.append(
            TableColumn(
                key="pivot_explanation",
                label=str(explanation_profile.label if explanation_profile else "Explanation"),
                width=(explanation_profile.width if explanation_profile else 50),
                wrap=(explanation_profile.wrap if explanation_profile else True),
                content_align="left",
            )
        )

    # =====================================================
    # Rows
    # =====================================================

    table_rows = []
    row_meta = []

    for entry in entries:
        # -------------------------------------------------
        # Section row
        # -------------------------------------------------

        if entry["kind"] == "section":
            section_name = entry["label"]

            # ---------------------------------------------
            # Spacer row
            # ---------------------------------------------

            if table_rows:
                table_rows.append(["" for _ in columns])
                row_meta.append(
                    {
                        "kind": "spacer",
                    }
                )

            # ---------------------------------------------
            # TOML-style section header
            # ---------------------------------------------

            parts = section_name.upper().split(".")

            section_lines = []

            for depth, part in enumerate(parts):
                indent = "  " * depth
                if depth == 0:
                    line = f"{indent}{part}"
                else:
                    line = f"{indent}.{part}"
                section_lines.append(line)

            section_label = "\n".join(section_lines)
            row = [section_label]
            row.extend([" " for _ in rows])

            if explain_enabled:
                row.append(" ")

            table_rows.append(row)
            row_meta.append(
                {
                    "kind": "section",
                }
            )

            continue

        # -------------------------------------------------
        # Field row
        # -------------------------------------------------

        elif entry["kind"] == "field":
            field_name = entry["field_name"]

            vals = [format_compare_value(v) for v in entry["values"]]

            row = [f"  {field_name}"]

            row.extend(vals)

            # ---------------------------------------------
            # Explanation column
            # ---------------------------------------------

            if explain_enabled:
                try:
                    explanation = build_explanation_cell(
                        field_name=entry["path"],
                        registry=registry,
                        catalog_index=catalog_index,
                        explain_facets=explain_facets,
                        row_values=vals,
                    )

                except Exception as ex:
                    explanation = f"[explain error: {type(ex).__name__}: {ex}]"

                row.append(
                    explanation,
                )

            table_rows.append(row)
            row_meta.append({})

    # =====================================================
    # Return table
    # =====================================================

    return RoostTable(
        columns=columns,
        rows=table_rows,
        row_meta=row_meta,
    )
