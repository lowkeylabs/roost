# src/owlroost/catalog/comparison/supersession.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.display.fields.identity import (
    compact_id_display,
)

from .structure import (
    rows_are_equivalent,
)

# =========================================================
# Helpers
# =========================================================


def _row_timestamp(
    row,
):
    return row.get(
        "_meta",
        {},
    ).get(
        "session.timestamp",
        "",
    )


# =========================================================
# Supersession
# =========================================================


def find_superseded_rows(
    dataset,
):
    """
    Detect superseded equivalent runs.

    Keeps newest equivalent run.

    Returns:

        [
            {
                "active": newest_row,
                "superseded": older_row,
            }
        ]
    """

    rows = sorted(
        dataset.rows,
        key=_row_timestamp,
        reverse=True,
    )

    superseded = []

    obsolete_ids = set()

    for i, row_a in enumerate(rows):
        row_a_id = compact_id_display(
            row_a,
        )

        if row_a_id in obsolete_ids:
            continue

        for row_b in rows[i + 1 :]:
            row_b_id = compact_id_display(
                row_b,
            )

            if row_b_id in obsolete_ids:
                continue

            if not rows_are_equivalent(
                row_a,
                row_b,
            ):
                continue

            active = row_a
            obsolete = row_b

            superseded.append(
                {
                    "active": active,
                    "superseded": obsolete,
                }
            )

            obsolete.setdefault(
                "_meta",
                {},
            )["is_superseded"] = True

            obsolete["_meta"]["superseded_by"] = compact_id_display(
                active,
            )

            obsolete_ids.add(
                compact_id_display(
                    obsolete,
                )
            )

    return superseded


def collect_superseded_rows(
    dataset,
):
    """
    Return rows safe to purge.
    """

    pairs = find_superseded_rows(
        dataset,
    )

    return [pair["superseded"] for pair in pairs]
