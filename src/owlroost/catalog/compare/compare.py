from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from owlroost.display.explain import (
    build_raw_field_explanation,
    normalize_explain_facets,
)
from owlroost.display.fields.identity import (
    compact_id_display,
)
from owlroost.display.table import (
    RoostTable,
    TableColumn,
)

# =========================================================
# Constants
# =========================================================

STRUCTURAL_COMPARE_EXCLUDES = {
    "description",
    "promotion",
}

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

    # -----------------------------------------------------
    # Path-like strings
    # -----------------------------------------------------

    if isinstance(value, str):
        # ---------------------------------------------
        # Show only basename for TOML files
        # ---------------------------------------------

        if value.endswith(".toml"):
            return str(Path(value).name)

        return value

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
    rows,
    diff_only=False,
):
    """
    Build ordered comparison entry structure.

    Preserves full TOML hierarchy.

    Produces:

        section:
            roost_runtime.auto_thread_policy

        field:
            solver
            workers_per_run
    """

    if not rows:
        return []

    # =====================================================
    # Build ordered union structure
    # =====================================================

    ordered_entries = []

    seen_entries = set()

    for row in rows:
        inputs = row.get(
            "_inputs",
            {},
        )

        entries = flatten_structure(
            inputs,
        )

        for entry in entries:
            if entry in seen_entries:
                continue

            ordered_entries.append(entry)

            seen_entries.add(entry)

    materialized = []

    emitted_sections = set()

    # =====================================================
    # Walk ordered structure
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
            # Ignore excluded fields/sections
            # ---------------------------------------------

            parts = value.split(".")

            if value in STRUCTURAL_COMPARE_EXCLUDES:
                continue

            if any(part in STRUCTURAL_COMPARE_EXCLUDES for part in parts):
                continue

            # ---------------------------------------------
            # Full TOML section
            # ---------------------------------------------

            if "." in value:
                split = value.rsplit(
                    ".",
                    1,
                )

                section_name = split[0]

                field_name = split[1]

            else:
                section_name = "_root"

                field_name = value

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
            # Emit section header
            # ---------------------------------------------

            if section_name != "_root" and section_name not in emitted_sections:
                emitted_sections.add(
                    section_name,
                )

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
                    "section": section_name,
                    "field_name": field_name,
                    "values": vals,
                }
            )

    return materialized


# =========================================================
# Equivalence / Supersession
# =========================================================


def rows_are_equivalent(
    row_a,
    row_b,
):
    """
    Return True if two rows are structurally equivalent.

    Uses EXACTLY the same semantics as --diff.
    """

    entries = build_compare_entries(
        [row_a, row_b],
        diff_only=True,
    )

    return len(entries) == 0


def _row_timestamp(
    row,
):
    return row.get("_meta", {}).get("session.timestamp", "")


def find_superseded_rows(
    dataset,
):
    """
    Detect superseded equivalent runs.

    Keeps newest equivalent run.

    Returns:
        [
            {
                "active": newest_row,
                "superseded": older_row,
            }
        ]
    """

    rows = sorted(
        dataset.rows,
        key=_row_timestamp,
        reverse=True,
    )

    superseded = []

    obsolete_ids = set()

    for i, row_a in enumerate(rows):
        row_a_id = compact_id_display(row_a)

        if row_a_id in obsolete_ids:
            continue

        for row_b in rows[i + 1 :]:
            row_b_id = compact_id_display(row_b)

            if row_b_id in obsolete_ids:
                continue

            # ---------------------------------------------
            # Structural equivalence
            # ---------------------------------------------

            if not rows_are_equivalent(
                row_a,
                row_b,
            ):
                continue

            # ---------------------------------------------
            # Keep newest
            # ---------------------------------------------

            active = row_a
            obsolete = row_b

            superseded.append(
                {
                    "active": active,
                    "superseded": obsolete,
                }
            )

            obsolete.setdefault(
                "_meta",
                {},
            )["is_superseded"] = True

            obsolete["_meta"]["superseded_by"] = compact_id_display(active)
            obsolete_ids.add(compact_id_display(obsolete))

    return superseded


def collect_superseded_rows(
    dataset,
):
    """
    Return rows safe to purge.
    """

    pairs = find_superseded_rows(
        dataset,
    )

    return [p["superseded"] for p in pairs]


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
