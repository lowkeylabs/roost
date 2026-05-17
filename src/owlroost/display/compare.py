# src/owlroost/display/compare.py

from __future__ import annotations

from copy import deepcopy

from owlroost.display.explain import (
    build_raw_field_explanation,
    normalize_explain_facets,
)
from owlroost.display.table import (
    RoostTable,
    TableColumn,
)

# =========================================================
# Constants
# =========================================================

STRUCTURAL_COMPARE_EXCLUDES = {"description", "case.file"}

# =========================================================
# Helpers
# =========================================================


def format_nested_list(
    value,
    indent=0,
):
    """
    Recursively format nested lists
    with line breaks.
    """

    # =====================================================
    # Non-list
    # =====================================================

    if not isinstance(value, list):
        if isinstance(value, float):
            return f"{value:g}"

        return str(value)

    # =====================================================
    # Flat list
    # =====================================================

    if not any(isinstance(x, list) for x in value):
        inner = ", ".join(format_nested_list(x) for x in value)

        return f"[{inner}]"

    # =====================================================
    # Nested list
    # =====================================================

    lines = []

    for item in value:
        lines.append(
            format_nested_list(
                item,
                indent + 2,
            )
        )

    return "\n".join(lines)


def format_compare_value(
    value,
):
    """
    Format arbitrary TOML value for comparison display.
    """

    if value is None:
        return ""

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, float):
        return f"{value:g}"

    if isinstance(value, list):
        return format_nested_list(
            value,
        )

    return str(value)


def flatten_structure(
    obj,
    prefix="",
    out=None,
    seen_sections=None,
):
    """
    Flatten nested TOML dict structure while preserving
    TOML ordering.

    Produces entries:

        ("section", "basic_info")
        ("field", "basic_info.status")

    Sections emitted only once.
    """

    if out is None:
        out = []

    if seen_sections is None:
        seen_sections = set()

    if not isinstance(obj, dict):
        return out

    for key, value in obj.items():
        full = key if not prefix else f"{prefix}.{key}"

        # -------------------------------------------------
        # Nested section
        # -------------------------------------------------

        if isinstance(value, dict):
            if full not in seen_sections:
                out.append(
                    (
                        "section",
                        full,
                    )
                )

                seen_sections.add(full)

            flatten_structure(
                value,
                prefix=full,
                out=out,
                seen_sections=seen_sections,
            )

        # -------------------------------------------------
        # Leaf field
        # -------------------------------------------------

        else:
            out.append(
                (
                    "field",
                    full,
                )
            )

    return out


def resolve_path(
    obj,
    path,
):
    """
    Resolve dotted path from nested dict.

    Returns None if missing.
    """

    current = obj

    for part in path.split("."):
        if not isinstance(current, dict):
            return None

        if part not in current:
            return None

        current = current[part]

    return current


def values_differ(
    values,
):
    """
    Return True if values differ across rows.
    """

    normalized = [deepcopy(v) for v in values]

    first = normalized[0]

    for v in normalized[1:]:
        if v != first:
            return True

    return False


# =========================================================
# Compare Matrix
# =========================================================


def build_compare_entries(
    dataset,
    diff_only=False,
):
    """
    Build ordered comparison entry structure.

    Preserves TOML ordering and section layout.

    In diff mode:
      - fields with identical values are omitted
      - section headers are emitted ONLY if at least
        one field in that section survives filtering
    """

    rows = dataset.rows

    if not rows:
        return []

    # =====================================================
    # Use first file as canonical structure ordering
    # =====================================================

    first_inputs = rows[0].get(
        "_inputs",
        {},
    )

    ordered_entries = flatten_structure(first_inputs)

    materialized = []

    emitted_sections = set()

    # =====================================================
    # Walk canonical ordered structure
    # =====================================================

    for kind, value in ordered_entries:
        # -------------------------------------------------
        # Section marker
        # -------------------------------------------------

        if kind == "section":
            continue

        # -------------------------------------------------
        # Field
        # -------------------------------------------------

        elif kind == "field":
            # ---------------------------------------------
            # Ignore excluded fields
            # ---------------------------------------------

            leaf = value.split(".")[-1]

            if value in STRUCTURAL_COMPARE_EXCLUDES or leaf in STRUCTURAL_COMPARE_EXCLUDES:
                continue

            # ---------------------------------------------
            # Determine section
            # ---------------------------------------------

            if "." in value:
                section_name = value.split(".")[0]

            else:
                section_name = "_root"

            # ---------------------------------------------
            # Collect values
            # ---------------------------------------------

            vals = []

            for row in rows:
                inputs = row.get(
                    "_inputs",
                    {},
                )

                vals.append(
                    resolve_path(
                        inputs,
                        value,
                    )
                )

            # ---------------------------------------------
            # Diff filtering
            # ---------------------------------------------

            if diff_only and not values_differ(vals):
                continue

            # ---------------------------------------------
            # Emit section header ONLY if field survives
            # ---------------------------------------------

            if section_name != "_root" and section_name not in emitted_sections:
                emitted_sections.add(section_name)

                materialized.append(
                    {
                        "kind": "section",
                        "label": section_name,
                    }
                )

            # ---------------------------------------------
            # Emit field row
            # ---------------------------------------------

            materialized.append(
                {
                    "kind": "field",
                    "path": value,
                    "values": vals,
                }
            )

    return materialized


# =========================================================
# Table Materialization
# =========================================================


def materialize_compare_table(
    dataset,
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

    rows = dataset.rows

    entries = build_compare_entries(
        dataset,
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
        case_name = row.get(
            "case_name",
            f"{i}",
        )

        columns.append(
            TableColumn(
                key=f"col_{i}",
                label=case_name,
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

    for entry in entries:
        # -------------------------------------------------
        # Section row
        # -------------------------------------------------

        if entry["kind"] == "section":
            section_name = entry["label"]

            # ---------------------------------------------
            # Spacer row between sections
            # ---------------------------------------------

            if table_rows:
                table_rows.append(["" for _ in columns])

            # ---------------------------------------------
            # Visible section header row
            # ---------------------------------------------

            section_label = f"[bold cyan]{section_name}[/bold cyan]"

            row = [section_label]

            row.extend([" " for _ in rows])

            if explain_facets:
                row.append(" ")

            table_rows.append(row)

            continue

        # -------------------------------------------------
        # Field row
        # -------------------------------------------------

        elif entry["kind"] == "field":
            full_path = entry["path"]

            # ==============================================
            # Render only leaf field name
            # ==============================================

            if "." in full_path:
                field_name = full_path.split(".")[-1]

            else:
                field_name = full_path

            vals = [format_compare_value(v) for v in entry["values"]]

            row = [f"  {field_name}"]

            row.extend(vals)

            # -------------------------------------------------
            # Explanation Cell
            # -------------------------------------------------

            if explain_facets:
                explanation = build_raw_field_explanation(
                    field_name,
                    explain_facets,
                )

                row.append(explanation)

            table_rows.append(row)

    # =====================================================
    # Return table
    # =====================================================

    return RoostTable(
        columns=columns,
        rows=table_rows,
    )
