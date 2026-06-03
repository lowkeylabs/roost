# src/owlroost/display/materializers/compare.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

# =========================================================
# Table Materialization
# =========================================================


def materialize_compare_table(
    rows,
    diff_only=False,
    explain=None,
):
    """
    Materialize structural compare/diff table.

    Returns RoostTable.
    """

    explain_facets = normalize_explain_facets(
        explain,
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

    if explain_facets:
        columns.append(
            TableColumn(
                key="explanation",
                label="Explanation",
                content_align="left",
                width=70,
                wrap=True,
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

            if explain_facets:
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

            if explain_facets:
                explanation = build_raw_field_explanation(
                    field_name,
                    explain_facets,
                )

                row.append(explanation)

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
