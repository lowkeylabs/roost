# src/owlroost/display/operations/dataset_ops.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

# =========================================================
# Dataset Utilities
# =========================================================


def attach_row_ids(
    dataset,
):
    """
    Attach stable row IDs.
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
