# src/owlroost/display/materialize.py

from __future__ import annotations

from owlroost.display.table import (
    RoostTable,
    TableColumn,
)
from owlroost.display.utils import (
    extract_path,
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

    Current scope:

    - case layer only
    - no aggregates
    - no pivot
    - no explainability
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

        profile = display_field.profiles.get(mode)

        # -------------------------------------------------
        # Label
        # -------------------------------------------------

        if profile and profile.label:
            label = profile.label

        else:
            label = field_name

        # -------------------------------------------------
        # Label Alignment
        # -------------------------------------------------

        if profile:
            label_align = profile.label_align

        else:
            label_align = "left"

        # -------------------------------------------------
        # Content Alignment
        # -------------------------------------------------

        if profile:
            content_align = profile.content_align

        else:
            content_align = "left"

        # -------------------------------------------------
        # Format
        # -------------------------------------------------

        if profile:
            fmt = profile.fmt

        else:
            fmt = None

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

            if display_field.display_fn:
                value = display_field.display_fn(dataset_row)

            # =================================================
            # Standard extracted value
            # =================================================

            else:
                value = extract_path(
                    dataset_row,
                    field_name,
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
