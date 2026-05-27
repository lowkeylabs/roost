from __future__ import annotations

from owlroost.display.operations.resolution import (
    resolve_row_value,
)


# =========================================================
# Canonical Sort
# =========================================================


def canonical_sort_key(
    row,
):
    """
    Canonical hierarchical ordering.
    """

    meta = row.get("_meta", {})

    return (
        meta.get("case_id", -1),
        meta.get("session_id", "-1"),
        meta.get("run_id", -1),
        meta.get("trial_id", -1),
    )


def apply_canonical_sort(
    rows,
):
    """
    Apply canonical ordering.
    """

    return sorted(
        rows,
        key=canonical_sort_key,
    )


# =========================================================
# Arbitrary Sort
# =========================================================


def apply_sort(
    rows,
    sort_key,
):
    """
    Sort rows by field.
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
            resolve_row_value(r, key)
            is None,
            resolve_row_value(r, key),
        ),
        reverse=descending,
    )
