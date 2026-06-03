# src/owlroost/display/materializers/materialize.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.display.explain import (
    build_field_explanation,
    normalize_explain_facets,
)
from owlroost.display.operations.profiles import (
    resolve_display_profile,
)
from owlroost.display.operations.resolution import (
    resolve_field_value,
)
from owlroost.display.registry import DisplayRegistry
from owlroost.display.renderers.specs import (
    RoostTable,
    TableColumn,
)

# =========================================================
# Entry Normalization
# =========================================================


def normalize_entry(
    entry,
):
    """
    Normalize all entry styles into dict form.

    Supported
    ---------

        "field_name"

        (
            "field_name",
            {
                "modes": ["pivot"],
                ...
            },
        )
    """

    # -----------------------------------------------------
    # Simple field
    # -----------------------------------------------------

    if isinstance(entry, str):
        return {
            "field": entry,
        }

    # -----------------------------------------------------
    # Decorated field
    # -----------------------------------------------------

    if (
        isinstance(entry, tuple)
        and len(entry) == 2
        and isinstance(entry[0], str)
        and isinstance(entry[1], dict)
    ):
        field_name, metadata = entry

        spec = {
            "field": field_name,
        }

        spec.update(
            metadata,
        )

        return spec

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
                "modes": ["table"],
            }
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
    registry: DisplayRegistry | None = None,
    explain_facets=None,
    catalog_index=None,
):
    """
    Flip rows/columns for pivot display.

    Notes
    -----
    Pivot rendering uses synthetic display
    fields:

        pivot_metric
        pivot_value
        pivot_explanation

    so pivot presentation participates in
    the normal display/profile system.
    """

    explain_enabled = bool(
        explain_facets,
    )

    # =====================================================
    # Synthetic Pivot Profiles
    # =====================================================

    metric_profile = None
    value_profile = None
    explanation_profile = None

    if registry is not None:
        try:
            metric_profile = resolve_display_profile(
                registry.get_display_field(
                    "pivot_metric",
                ),
                mode="pivot",
            )
        except KeyError:
            pass

        try:
            value_profile = resolve_display_profile(
                registry.get_display_field(
                    "pivot_value",
                ),
                mode="pivot",
            )
        except KeyError:
            pass

        try:
            explanation_profile = resolve_display_profile(
                registry.get_display_field(
                    "pivot_explanation",
                ),
                mode="pivot",
            )
        except KeyError:
            pass

    # =====================================================
    # New Columns
    # =====================================================

    new_columns = [
        TableColumn(
            key="pivot_metric",
            label=str(metric_profile.label if metric_profile is not None else "Metric"),
            width=(metric_profile.width if metric_profile else 25),
            wrap=(metric_profile.wrap if metric_profile else True),
            content_align="left",
        )
    ]

    for idx, _ in enumerate(
        table.rows,
    ):
        new_columns.append(
            TableColumn(
                key=str(idx),
                label=str(idx),
                width=(value_profile.width if value_profile else 80),
                wrap=(value_profile.wrap if value_profile else True),
                content_align="right",
            )
        )

    # =====================================================
    # Optional Explanation Column
    # =====================================================

    if explain_enabled:
        new_columns.append(
            TableColumn(
                key="pivot_explanation",
                label=str(explanation_profile.label if explanation_profile else "Explanation"),
                width=(explanation_profile.width if explanation_profile else 50),
                wrap=(explanation_profile.wrap if explanation_profile else True),
                content_align="left",
            )
        )

    # =====================================================
    # New Rows
    # =====================================================

    new_rows = []

    new_row_meta = []

    for col_idx, column in enumerate(
        table.columns,
    ):
        row = [
            column.label,
        ]

        row_values = []

        for original_row in table.rows:
            value = original_row[col_idx]

            row.append(
                value,
            )

            row_values.append(
                value,
            )

        # -------------------------------------------------
        # Explanation Cell
        # -------------------------------------------------

        if explain_enabled:
            explanation = ""

            try:
                display_field = getattr(
                    column,
                    "display_field",
                    None,
                )

                catalog_row = None

                if catalog_index is not None:
                    catalog_row = catalog_index.get(
                        column.field_name,
                    )

                explanation = build_field_explanation(
                    display_field=display_field,
                    catalog_row=catalog_row,
                    explain_facets=explain_facets,
                    row_values=row_values,
                )

            except Exception as ex:
                explanation = f"[explain error: {ex}]"

            row.append(
                explanation,
            )

        new_rows.append(
            row,
        )

        # -------------------------------------------------
        # Preserve Original Column Metadata
        # -------------------------------------------------

        new_row_meta.append(
            {
                "column": column,
                "field_name": column.key,
            }
        )

    return RoostTable(
        columns=new_columns,
        rows=new_rows,
        row_meta=new_row_meta,
    )


# =========================================================
# Materialization
# =========================================================


def materialize_view(
    *,
    rows,
    registry,
    catalog_index=None,
    view_name,
    level="case",
    mode="table",
    explain=None,
):
    """
    Materialize rows + view into a RoostTable.

    Responsibilities
    ----------------
    - resolve DisplayView
    - expand DisplayGroups
    - apply visibility rules
    - resolve DisplayFields
    - resolve row values
    - construct renderer-facing RoostTable

    Does NOT
    --------
    - render output
    - aggregate rows
    - discover rows
    """

    explain_facets = normalize_explain_facets(
        explain,
    )

    # =====================================================
    # Resolve View
    # =====================================================

    view = registry.get_view(
        level,
        view_name,
    )

    # =====================================================
    # Explain Requires Pivot
    # =====================================================

    if explain_facets and mode != "pivot":
        raise ValueError("--explain requires pivot mode")

    # =====================================================
    # Expand View
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
        modes = entry.get(
            "modes",
        )

        if modes is not None:
            if mode not in modes:
                continue

        visible_entries.append(
            entry,
        )

    # =====================================================
    # Field Names
    # =====================================================

    field_names = [entry["field"] for entry in visible_entries]

    # =====================================================
    # Columns
    # =====================================================

    columns: list[TableColumn] = []

    for field_name in field_names:
        display_field = registry.get_display_field(
            field_name,
        )

        profile = resolve_display_profile(
            display_field,
            mode=mode,
        )

        columns.append(
            TableColumn(
                key=field_name,
                field_name=field_name,
                label=(profile.label or field_name),
                label_align=profile.label_align,
                content_align=profile.content_align,
                fmt=profile.fmt,
                width=profile.width,
                wrap=profile.wrap,
                # =========================
                # Explain Metadata
                # =========================
                display_field=display_field,
                # catalog_spec=display_field.catalog_spec,
            )
        )

    # =====================================================
    # Rows
    # =====================================================

    materialized_rows = []

    row_meta = []

    for source_row in rows:
        materialized_row = []

        for field_name in field_names:
            display_field = registry.get_display_field(
                field_name,
            )

            value = resolve_field_value(
                row=source_row,
                field_name=field_name,
                display_field=display_field,
            )

            materialized_row.append(
                value,
            )

        materialized_rows.append(
            materialized_row,
        )

        meta = {
            "row": source_row,
        }

        if source_row.get(
            "_meta",
            {},
        ).get(
            "is_superseded",
        ):
            meta["dim"] = True

        row_meta.append(
            meta,
        )

    # =====================================================
    # Table
    # =====================================================

    table = RoostTable(
        columns=columns,
        rows=materialized_rows,
        row_meta=row_meta,
    )

    # =====================================================
    # Pivot
    # =====================================================

    if mode == "pivot":
        table = pivot_table(
            table,
            registry=registry,
            explain_facets=explain_facets,
            catalog_index=catalog_index,
        )

    return table
