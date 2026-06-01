# src/owlroost/operations/delete.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

import shutil
from pathlib import Path

# =========================================================
# Delete Target Resolution
# =========================================================


def collect_delete_targets(
    rows,
    level,
):
    """
    Resolve filesystem targets from dataset rows.
    """

    targets = []

    for row in rows:
        paths = row.get("_paths", {})

        if level == "case":
            target = paths.get("case_dir")

        elif level == "session":
            target = paths.get("session_dir")

        elif level == "run":
            target = paths.get("run_dir")

        else:
            raise ValueError(f"Delete not supported for level: {level}")

        if target is not None:
            targets.append(Path(target))

    # Deduplicate + stable ordering
    return sorted(set(targets))


# =========================================================
# Delete Execution
# =========================================================


def delete_paths(
    paths,
):
    """
    Delete filesystem targets.

    After deletion:
        - prune empty sessions
        - prune empty date dirs
        - prune empty case dirs
    """

    deleted = []

    results_roots = set()

    for path in paths:
        path = Path(path).resolve()

        if not path.exists():
            continue

        # ----------------------------------------
        # Locate results root
        # ----------------------------------------

        results_root = find_results_root(
            path,
        )

        if results_root:
            results_roots.add(
                results_root,
            )

        # ----------------------------------------
        # Delete target
        # ----------------------------------------

        shutil.rmtree(path)

        deleted.append(path)

    # =====================================================
    # Cleanup empty operational containers
    # =====================================================

    for results_root in results_roots:
        prune_empty_sessions(
            results_root,
        )

    return deleted


# =========================================================
# Results Root Discovery
# =========================================================


def find_results_root(
    path,
):
    """
    Locate ancestor named 'results'.
    """

    path = Path(path).resolve()

    for parent in [path] + list(path.parents):
        if parent.name == "results":
            return parent

    return None


# =========================================================
# Session Validation
# =========================================================


def session_has_runs(
    session_dir,
):
    """
    Return True if session contains run_* dirs.
    """

    session_dir = Path(session_dir)

    return any(p.is_dir() and p.name.startswith("run_") for p in session_dir.iterdir())


# =========================================================
# Cleanup
# =========================================================


def prune_empty_sessions(
    results_root,
):
    """
    Remove empty operational containers.

    Hierarchy:

        results/<case>/<date>/<session>/run_X

    Rules:

        - sessions without run_* are removed
        - empty date dirs are removed
        - empty case dirs are removed
    """

    results_root = Path(results_root).resolve()

    if not results_root.exists():
        return

    # =====================================================
    # Cases
    # =====================================================

    for case_dir in results_root.iterdir():
        if not case_dir.is_dir():
            continue

        # =================================================
        # Dates
        # =================================================

        for date_dir in case_dir.iterdir():
            if not date_dir.is_dir():
                continue

            # =============================================
            # Sessions
            # =============================================

            for session_dir in date_dir.iterdir():
                if not session_dir.is_dir():
                    continue

                # ----------------------------------------
                # Remove empty sessions
                # ----------------------------------------

                if not session_has_runs(
                    session_dir,
                ):
                    shutil.rmtree(
                        session_dir,
                    )

            # =============================================
            # Remove empty date dirs
            # =============================================

            if not any(date_dir.iterdir()):
                date_dir.rmdir()

        # =================================================
        # Remove empty case dirs
        # =================================================

        if not any(case_dir.iterdir()):
            case_dir.rmdir()
