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
# View Expansion
# =========================================================


def expand_view_entries(
    registry,
    entries,
):
    """
    Expand view/group entries into
    a flat ordered field list.

    Example:

        [
            ("group", "identity"),
            "runtime.trial_jobs",
        ]

    becomes:

        [
            "case_name",
            "description",
            "runtime.trial_jobs",
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

        # =================================================
        # STRING FIELD
        # =================================================

        elif isinstance(entry, str):
            out.append(entry)

        # =================================================
        # EXPLICIT FIELD
        # =================================================

        elif isinstance(entry, tuple) and len(entry) == 2 and entry[0] == "field":
            out.append(entry[1])

        # =================================================
        # UNKNOWN
        # =================================================

        else:
            raise ValueError(f"Unsupported view entry: {entry}")

    return out


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
    # Expand Groups
    # =====================================================

    field_names = expand_view_entries(
        registry,
        view.entries,
    )

    # =====================================================
    # Build Columns
    # =====================================================

    columns = []

    for field_name in field_names:
        display_field = registry.get_display_field(field_name)

        profile = display_field.profiles.get(mode) or DisplayProfile()

        label = profile.label or field_name
        label_align = profile.label_align
        content_align = profile.content_align
        fmt = profile.fmt

        # -------------------------------------------------
        # Build Column
        # -------------------------------------------------

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

            # =================================================
            # Display-derived value
            # =================================================

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

    return RoostTable(
        columns=columns,
        rows=rows,
    )
