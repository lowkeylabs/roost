# src/owlroost/display/materialize.py

from __future__ import annotations

from owlroost.display.specs import DisplayProfile
from owlroost.display.table import (
    RoostTable,
    TableColumn,
)
from owlroost.display.utils import (
    resolve_field_value,
)

# =========================================================
# Visibility
# =========================================================


def build_visibility_context(
    mode,
):
    """
    Build visibility context flags.
    """

    return {
        "is_table": mode == "table",
        "is_pivot": mode == "pivot",
    }


def entry_is_visible(
    entry,
    visibility,
):
    """
    Evaluate show_if visibility.
    """

    show_if = entry.get("show_if")

    if not show_if:
        return True

    if isinstance(show_if, str):
        show_if = [show_if]

    return all(visibility.get(flag, False) for flag in show_if)


# =========================================================
# Entry Normalization
# =========================================================


def normalize_entry(
    entry,
):
    """
    Normalize all entry styles into dict form.

    Supported:

        "field_name"

        ("field", "field_name")

        {
            "field": "field_name",
            "show_if": ...
        }
    """

    # -----------------------------------------------------
    # Simple string
    # -----------------------------------------------------

    if isinstance(entry, str):
        return {
            "field": entry,
        }

    # -----------------------------------------------------
    # Explicit tuple field
    # -----------------------------------------------------

    if isinstance(entry, tuple) and len(entry) == 2 and entry[0] == "field":
        return {
            "field": entry[1],
        }

    # -----------------------------------------------------
    # Already normalized
    # -----------------------------------------------------

    if isinstance(entry, dict):
        if "field" not in entry:
            raise ValueError(f"Entry dict missing 'field': {entry}")

        return entry

    raise ValueError(f"Unsupported entry: {entry}")


# =========================================================
# View Expansion
# =========================================================


def expand_view_entries(
    registry,
    entries,
):
    """
    Expand view/group entries into
    a flat ordered list of normalized entry specs.

    Output format:

        [
            {
                "field": "case_name",
            },
            {
                "field": "compact_id",
                "show_if": ["is_table"],
            },
        ]
    """

    out = []

    for entry in entries:
        # =================================================
        # GROUP
        # =================================================

        if isinstance(entry, tuple) and len(entry) == 2 and entry[0] == "group":
            group_name = entry[1]

            group = registry.get_group(group_name)

            out.extend(
                expand_view_entries(
                    registry,
                    group.entries,
                )
            )

            continue

        # =================================================
        # Normalize
        # =================================================

        spec = normalize_entry(entry)

        out.append(spec)

    return out


# =========================================================
# Pivot Transform
# =========================================================


def pivot_table(
    table,
):
    """
    Flip rows/columns for pivot display.
    """

    # -----------------------------------------------------
    # New Columns
    # -----------------------------------------------------

    new_columns = [
        TableColumn(
            key="metric",
            label="Metric",
        )
    ]

    for idx, _ in enumerate(table.rows):
        new_columns.append(
            TableColumn(
                key=str(idx),
                label=str(idx),
                content_align="right",
            )
        )

    # -----------------------------------------------------
    # New Rows
    # -----------------------------------------------------

    new_rows = []

    new_row_meta = []

    for col_idx, column in enumerate(table.columns):
        row = [column.label]

        for original_row in table.rows:
            row.append(original_row[col_idx])

        new_rows.append(row)

        # Preserve original column metadata
        new_row_meta.append(column)

    return RoostTable(
        columns=new_columns,
        rows=new_rows,
        row_meta=new_row_meta,
    )


# =========================================================
# Materialization
# =========================================================


def materialize_view(
    dataset,
    registry,
    level,
    view_name,
    mode="table",
):
    """
    Materialize dataset + view into RoostTable.

    Responsibilities:
    - expand view/group definitions
    - resolve display fields
    - resolve semantic values
    - build renderer-facing tables

    Does NOT:
    - aggregate datasets
    - pivot tables
    - render output
    """

    # =====================================================
    # Resolve View
    # =====================================================

    view = registry.get_view(
        level,
        view_name,
    )

    # =====================================================
    # Visibility Context
    # =====================================================

    visibility = build_visibility_context(mode)

    # =====================================================
    # Expand Groups
    # =====================================================

    expanded_entries = expand_view_entries(
        registry,
        view.entries,
    )

    # =====================================================
    # Apply Visibility
    # =====================================================

    visible_entries = []

    for entry in expanded_entries:
        if entry_is_visible(
            entry,
            visibility,
        ):
            visible_entries.append(entry)

    # =====================================================
    # Final Field Names
    # =====================================================

    field_names = [entry["field"] for entry in visible_entries]

    # =====================================================
    # Build Columns
    # =====================================================

    columns = []

    for field_name in field_names:
        display_field = registry.get_display_field(field_name)

        profile = (
            display_field.profiles.get(mode)
            or display_field.profiles.get("table")
            or DisplayProfile()
        )

        label = profile.label or field_name
        label_align = profile.label_align
        content_align = profile.content_align
        fmt = profile.fmt

        columns.append(
            TableColumn(
                key=field_name,
                label=label,
                label_align=label_align,
                content_align=content_align,
                fmt=fmt,
            )
        )

    # =====================================================
    # Build Rows
    # =====================================================

    rows = []

    for dataset_row in dataset.rows:
        row = []

        for field_name in field_names:
            display_field = registry.get_display_field(field_name)

            value = resolve_field_value(
                row=dataset_row,
                field_name=field_name,
                display_field=display_field,
            )

            row.append(value)

        rows.append(row)

    # =====================================================
    # Final Table
    # =====================================================

    table = RoostTable(
        columns=columns,
        rows=rows,
    )

    # =====================================================
    # Pivot
    # =====================================================

    if mode == "pivot":
        table = pivot_table(table)

    return table
