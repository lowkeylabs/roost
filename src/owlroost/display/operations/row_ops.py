# src/owlroost/display/operations/row_ops.py

"""
Row operations.

Notes
-----
Utilities operating on catalog rows and
result rows.

These helpers intentionally operate on:

    list[dict]

rather than Dataset abstractions.
"""

from __future__ import annotations

# =========================================================
# Row IDs
# =========================================================


def attach_row_ids(
    rows,
):
    """
    Attach stable row IDs.

    Returns
    -------
    New row list with contiguous IDs.
    """

    output = []

    for i, row in enumerate(rows):
        new_row = dict(row)

        new_row["_row_id"] = i

        output.append(
            new_row,
        )

    return output


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
