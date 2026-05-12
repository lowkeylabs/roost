# src/owlroost/display/utils.py

from __future__ import annotations

from owlroost.display.table import (
    TableColumn,
)

# =========================================================
# Path Extraction
# =========================================================


def extract_path(
    data,
    path,
):
    """
    Extract dotted path from _inputs.

    Example:
        optimization.objective
    """

    # -----------------------------------------------------
    # Special path
    # -----------------------------------------------------

    if path == "_path":
        return str(data["_path"])

    # -----------------------------------------------------
    # Inputs root
    # -----------------------------------------------------

    cur = data.get(
        "_inputs",
        {},
    )

    # -----------------------------------------------------
    # Traverse dotted path
    # -----------------------------------------------------

    for p in path.split("."):
        if not isinstance(
            cur,
            dict,
        ):
            return None

        cur = cur.get(p)

        if cur is None:
            return None

    return cur


# =========================================================
# Semantic Field Resolution
# =========================================================


def resolve_field_value(
    row,
    field_name,
    display_field=None,
):
    """
    Resolve field value from dataset row.

    Resolution order:
    - display_fn
    - _metrics
    - _inputs
    - top-level row

    This becomes the canonical value
    resolution layer for:
    - tables
    - pivot
    - explain
    - reports
    """

    # -----------------------------------------------------
    # Display-derived value
    # -----------------------------------------------------

    if display_field and display_field.display_fn:
        return display_field.display_fn(row)

    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------

    metrics = row.get(
        "_metrics",
        {},
    )

    if field_name in metrics:
        return metrics[field_name]

    # -----------------------------------------------------
    # Inputs
    # -----------------------------------------------------

    value = extract_path(
        row,
        field_name,
    )

    if value is not None:
        return value

    # -----------------------------------------------------
    # Top-level row
    # -----------------------------------------------------

    return row.get(field_name)


# =========================================================
# Dataset Utilities
# =========================================================


def attach_row_ids(dataset):
    """
    Attach stable row IDs to dataset.
    """

    rows = []

    for i, r in enumerate(dataset.rows):
        new = dict(r)

        new["_row_id"] = i

        rows.append(new)

    return type(dataset)(
        rows,
        level=dataset.level,
    )


# =========================================================
# Table Utilities
# =========================================================


def inject_id_column(
    table,
    dataset,
):
    """
    Inject dataset row IDs into rendered table.

    Assumes table.columns contains fully
    materialized TableColumn objects.
    """

    # =====================================================
    # Insert Column
    # =====================================================

    table.columns = [
        TableColumn(
            key="_row_id",
            label="ID",
            label_align="right",
            content_align="right",
        )
    ] + list(table.columns)

    # =====================================================
    # Insert Row Values
    # =====================================================

    new_rows = []

    for row_data, r in zip(
        table.rows,
        dataset.rows,
        strict=False,
    ):
        new_rows.append([str(r["_row_id"])] + list(row_data))

    table.rows = new_rows

    return table
