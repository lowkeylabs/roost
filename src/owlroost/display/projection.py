# src/owlroost/display/projection.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from collections import defaultdict

# =========================================================
# Public API
# =========================================================


def project_dataset(
    dataset,
    level,
):
    """
    Project dataset into operational hierarchy level.

    Levels:
        run
        session
        case
    """

    if level == dataset.level:
        return dataset

    if level == "run":
        return dataset

    if level == "session":
        return project_run_to_session(dataset)

    if level == "case":
        return project_run_to_case(dataset)

    raise ValueError(f"Unsupported projection level: {level}")


# =========================================================
# Session Projection
# =========================================================


def project_run_to_session(
    dataset,
):
    """
    Aggregate run rows into session provenance rows.

    Sessions are operational containers,
    not statistical entities.
    """

    groups = defaultdict(list)

    for row in dataset.rows:
        meta = row.get("_meta", {})

        key = (
            meta.get("case_id"),
            meta.get("session_id"),
        )

        groups[key].append(row)

    rows = []

    for (case_id, session_id), run_rows in sorted(groups.items()):
        first = run_rows[0]

        paths = first["_paths"]
        session_dir = paths["session_dir"]
        date_dir = paths["date_dir"]
        case_dir = paths["case_dir"]
        results_root = paths["results_root"]
        session_date = paths["session_date"]
        session_time = paths["session_time"]
        session_timestamp = paths["session_timestamp"]

        run_count = len(run_rows)

        total_trials = sum(r.get("_metrics", {}).get("trial.total", 0) for r in run_rows)

        completed_trials = sum(r.get("_metrics", {}).get("trial.completed", 0) for r in run_rows)

        pending_trials = sum(r.get("_metrics", {}).get("trial.pending", 0) for r in run_rows)

        rows.append(
            {
                "_path": session_dir.resolve(),
                "_paths": {
                    "results_root": results_root,
                    "case_dir": case_dir,
                    "date_dir": date_dir,
                    "session_dir": session_dir,
                },
                "_inputs": {
                    "case_name": case_dir.name,
                },
                "_metrics": {
                    "run.count": run_count,
                    "trial.total": total_trials,
                    "trial.completed": completed_trials,
                    "trial.pending": pending_trials,
                },
                "_meta": {
                    "level": "session",
                    "case_id": case_id,
                    "session_id": session_id,
                    "session.date": session_date,
                    "session.time": session_time,
                    "session.timestamp": session_timestamp,
                },
            }
        )

    return Dataset(
        rows,
        level="session",
    )


# =========================================================
# Case Projection
# =========================================================


def project_run_to_case(
    dataset,
):
    """
    Aggregate run rows into case provenance rows.
    """

    groups = defaultdict(list)

    for row in dataset.rows:
        case_id = row.get("_meta", {}).get("case_id")

        groups[case_id].append(row)

    rows = []

    for case_id, run_rows in sorted(groups.items()):
        first = run_rows[0]

        paths = first["_paths"]
        case_dir = paths["case_dir"]
        results_root = paths["results_root"]
        case_name = case_dir.name

        session_keys = {
            (
                r["_meta"].get("case_id"),
                r["_meta"].get("session_id"),
            )
            for r in run_rows
        }

        rows.append(
            {
                "_path": case_dir,
                "_paths": {
                    "results_root": results_root,
                    "case_dir": case_dir,
                },
                "_inputs": {
                    "case_name": case_name,
                },
                "_metrics": {
                    "session.count": len(session_keys),
                    "run.count": len(run_rows),
                    "trial.total": sum(
                        r.get("_metrics", {}).get("trial.total", 0) for r in run_rows
                    ),
                },
                "_meta": {
                    "level": "case",
                    "case_id": case_id,
                },
            }
        )

    return Dataset(
        rows,
        level="case",
    )
