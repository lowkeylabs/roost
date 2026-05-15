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
    - explicit path lookup
    - _metrics
    - _meta
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

    if display_field is not None and display_field.display_fn:
        return display_field.display_fn(row)

    # -----------------------------------------------------
    # Explicit storage path
    # -----------------------------------------------------

    if display_field is not None and display_field.path is not None:
        value = extract_path(
            row,
            display_field.path,
        )

        if value is not None:
            return value

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
    # Meta
    # -----------------------------------------------------

    meta = row.get(
        "_meta",
        {},
    )

    if field_name in meta:
        return meta[field_name]

    # -----------------------------------------------------
    # Inputs
    # -----------------------------------------------------

    value = extract_path(
        row.get("_inputs", {}),
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


# =========================================================
# Row Value Resolution
# =========================================================


def resolve_row_value(
    row,
    key,
):
    """
    Resolve value from dataset row.

    Search order:
        _meta
        _metrics
        _inputs (dotted path)
    """

    # -----------------------------------------------------
    # _meta
    # -----------------------------------------------------

    if key in row.get("_meta", {}):
        return row["_meta"][key]

    # -----------------------------------------------------
    # _metrics
    # -----------------------------------------------------

    if key in row.get("_metrics", {}):
        return row["_metrics"][key]

    # -----------------------------------------------------
    # _inputs dotted path
    # -----------------------------------------------------

    current = row.get("_inputs", {})

    for part in key.split("."):
        if not isinstance(current, dict):
            return None

        if part not in current:
            return None

        current = current[part]

    return current


# =========================================================
# Filtering
# =========================================================


def parse_filter_expression(
    expr,
):
    """
    Parse expressions like:

        case_id=0
        trial.completed>50
        success_rate>=0.9
    """

    operators = [
        "=in:",
        ">=",
        "<=",
        "!=",
        ">",
        "<",
        "=",
    ]

    for op in operators:
        if op in expr:
            left, right = expr.split(op, 1)

            return (
                left.strip(),
                op,
                right.strip(),
            )

    raise ValueError(f"Invalid filter expression: {expr}")


def coerce_value(
    value,
):
    """
    Attempt numeric coercion.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (
            int,
            float,
        ),
    ):
        return value

    s = str(value)

    try:
        if "." in s:
            return float(s)

        return int(s)

    except Exception:
        return s


def compare_values(
    lhs,
    op,
    rhs,
):
    """
    Compare values using operator.
    """

    lhs = coerce_value(lhs)

    # =====================================================
    # Membership
    # =====================================================

    if op == "=in:":
        values = [coerce_value(x.strip()) for x in str(rhs).split(",") if x.strip()]

        return lhs in values

    # =====================================================
    # Standard coercion
    # =====================================================

    rhs = coerce_value(rhs)

    if op == "=":
        return lhs == rhs

    if op == "!=":
        return lhs != rhs

    if op == ">":
        return lhs > rhs

    if op == "<":
        return lhs < rhs

    if op == ">=":
        return lhs >= rhs

    if op == "<=":
        return lhs <= rhs

    raise ValueError(f"Unsupported operator: {op}")


def apply_filters(
    rows,
    filters,
):
    """
    Apply CLI filters.
    """

    if not filters:
        return rows

    out = []

    parsed = [parse_filter_expression(f) for f in filters]

    for row in rows:
        keep = True

        for key, op, rhs in parsed:
            lhs = resolve_row_value(
                row,
                key,
            )

            if not compare_values(lhs, op, rhs):
                keep = False
                break

        if keep:
            out.append(row)

    return out


# =========================================================
# Sorting
# =========================================================


def canonical_sort_key(
    row,
):
    """
    Canonical default ordering.

    Order:
        case_id
        experiment_id
        run_id
        trial_id
    """

    meta = row.get(
        "_meta",
        {},
    )

    case_id = meta.get(
        "case_id",
        -1,
    )

    experiment_id = meta.get(
        "experiment_id",
        "",
    )

    run_id = meta.get(
        "run_id",
        -1,
    )

    trial_id = meta.get(
        "trial_id",
        -1,
    )

    return (
        case_id,
        experiment_id,
        run_id,
        trial_id,
    )


def apply_canonical_sort(
    rows,
):
    """
    Apply canonical hierarchical ordering.

    Order:
        case_id
        experiment_id
        run_id
        trial_id
    """

    return sorted(
        rows,
        key=canonical_sort_key,
    )


def apply_sort(
    rows,
    sort_key,
):
    """
    Sort rows by field.

    Prefix '-' for descending.

    Examples:
        trial.completed
        -trial.completed
    """

    if not sort_key:
        return rows

    descending = False

    key = sort_key

    if sort_key.startswith("-"):
        descending = True
        key = sort_key[1:]

    return sorted(
        rows,
        key=lambda r: (
            resolve_row_value(r, key) is None,
            resolve_row_value(r, key),
        ),
        reverse=descending,
    )


# =========================================================
# Top-N
# =========================================================


def apply_top(
    rows,
    top_n,
):
    """
    Limit rows.
    """

    if top_n is None:
        return rows

    return rows[:top_n]
