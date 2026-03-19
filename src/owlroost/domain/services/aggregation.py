from __future__ import annotations

import statistics


def aggregate_rows(rows: list[dict]) -> dict:
    """
    Generic aggregation over trial rows.
    Returns a flat dict of aggregated values.
    """

    if not rows:
        return {}

    total = len(rows)

    # -----------------------------
    # Status
    # -----------------------------
    solved = [r for r in rows if r.get("status") == "solved"]
    failed = [r for r in rows if r.get("status") == "failed"]

    success_rate = len(solved) / total if total else 0.0
    fail_rate = len(failed) / total if total else 0.0

    # -----------------------------
    # Numeric helpers
    # -----------------------------
    def numeric_values(key, subset=None):
        subset = subset or rows
        return [r[key] for r in subset if isinstance(r.get(key), (int | float))]

    # -----------------------------
    # Bequest
    # -----------------------------
    bequests = numeric_values("bequest", solved)

    avg_bequest = statistics.mean(bequests) if bequests else None
    med_bequest = statistics.median(bequests) if bequests else None

    # -----------------------------
    # Time
    # -----------------------------
    times = numeric_values("elapsed")

    avg_time = statistics.mean(times) if times else None

    # -----------------------------
    # Risk distribution
    # -----------------------------
    risk_counts = {}
    for r in solved:
        risk = r.get("risk")
        if risk:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

    return {
        "trial_count": total,
        "success_rate": success_rate,
        "fail_rate": fail_rate,
        "avg_bequest": avg_bequest,
        "median_bequest": med_bequest,
        "avg_time": avg_time,
        "risk_counts": risk_counts,
    }
