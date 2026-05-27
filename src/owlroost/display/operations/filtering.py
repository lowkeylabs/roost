from __future__ import annotations

from owlroost.display.operations.resolution import (
    resolve_row_value,
)


# =========================================================
# Parsing
# =========================================================


def parse_filter_expression(
    expr,
):
    """
    Parse filter expression.
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

    raise ValueError(
        f"Invalid filter expression: {expr}"
    )


# =========================================================
# Value Coercion
# =========================================================


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


# =========================================================
# Comparison
# =========================================================


def compare_values(
    lhs,
    op,
    rhs,
):
    """
    Compare values using filter operator.
    """

    lhs = coerce_value(lhs)

    # =====================================================
    # Membership
    # =====================================================

    if op == "=in:":
        values = [
            coerce_value(x.strip())
            for x in str(rhs).split(",")
            if x.strip()
        ]

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

    raise ValueError(
        f"Unsupported operator: {op}"
    )


# =========================================================
# Filtering
# =========================================================


def apply_filters(
    rows,
    filters,
):
    """
    Apply row filters.
    """

    if not filters:
        return rows

    parsed = [
        parse_filter_expression(f)
        for f in filters
    ]

    out = []

    for row in rows:
        keep = True

        for key, op, rhs in parsed:
            lhs = resolve_row_value(
                row,
                key,
            )

            if not compare_values(
                lhs,
                op,
                rhs,
            ):
                keep = False
                break

        if keep:
            out.append(row)

    return out
