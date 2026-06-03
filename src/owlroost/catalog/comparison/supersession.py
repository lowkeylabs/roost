# src/owlroost/catalog/comparison/supersession.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

# from owlroost.display.fields.identity import (
#    compact_id_display,
# )
from .structure import (
    rows_are_equivalent,
)

# =========================================================
# Helpers
# =========================================================


def compact_id_display(
    row,
):
    """
    Return compact hierarchical identifier.

    Examples:

        Case:
            0

        Session:
            0/1

        Run:
            0/1/0

        Trial:
            0/1/0/12
    """

    try:
        meta = row.get(
            "_meta",
            {},
        )

        case_id = meta.get(
            "case_id",
        )

        session_id = meta.get(
            "session_id",
        )

        run_id = meta.get(
            "run_id",
        )

        trial_id = meta.get(
            "trial_id",
        )

        # =================================================
        # Missing Core IDs
        # =================================================

        if case_id is None:
            return None

        # =================================================
        # Case Level
        # =================================================

        if session_id is None:
            return f"{case_id}"

        # =================================================
        # Session Level
        # =================================================

        if run_id is None:
            return f"{case_id}/{session_id}"

        # =================================================
        # Run Level
        # =================================================

        if trial_id is None:
            return f"{case_id}/{session_id}/{run_id}"

        # =================================================
        # Trial Level
        # =================================================

        return f"{case_id}/{session_id}/{run_id}/{trial_id}"

    except Exception:
        return None


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
    input_rows,
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
        input_rows,
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
    rows,
):
    """
    Return rows safe to purge.
    """

    pairs = find_superseded_rows(
        rows,
    )

    return [pair["superseded"] for pair in pairs]
