# src/owlroost/display/discovery/results_tree.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from pathlib import Path


# =========================================================
# Cases
# =========================================================
def find_cases(results_root: Path):
    """
    Find case directories.

    Layout:
        results/<case_name>/
    """

    results_root = Path(results_root)

    if not results_root.exists():
        return []

    out = []

    for p in results_root.iterdir():
        if p.is_dir():
            out.append(p.resolve())

    return sorted(out)


# =========================================================
# Sessions
# =========================================================
def find_sessions(results_root: Path):
    """
    Find session directories.

    Layout:
        results/<case>/<date>/<time>/

    Session identification:
        contains multirun.yaml and session.toml
    """

    out = []

    for case_dir in find_cases(results_root):
        for date_dir in case_dir.iterdir():
            if not date_dir.is_dir():
                continue

            for exp_dir in date_dir.iterdir():
                if not exp_dir.is_dir():
                    continue

                if (exp_dir / "multirun.yaml").exists():
                    out.append(exp_dir.resolve())

    return sorted(out)


# =========================================================
# Runs
# =========================================================
def find_runs(exp_dir: Path):
    """
    Find run directories.

    Layout:
        session/run_*
    """

    exp_dir = Path(exp_dir)

    if not exp_dir.exists():
        return []

    out = []

    for p in exp_dir.iterdir():
        if not p.is_dir():
            continue

        if p.name.startswith("run_"):
            out.append(p.resolve())

    return sorted(out)


def find_all_runs(results_root: Path):
    """
    Find all runs beneath results root.
    """

    out = []

    for exp_dir in find_sessions(results_root):
        out.extend(find_runs(exp_dir))

    return sorted(out)


# =========================================================
# Trials
# =========================================================
def find_trials(run_dir: Path):
    """
    Find trial directories.

    Layout:
        run_dir/trials/0000
    """

    run_dir = Path(run_dir)

    trials_dir = run_dir / "trials"

    if not trials_dir.exists():
        return []

    out = []

    for p in trials_dir.iterdir():
        if p.is_dir():
            out.append(p.resolve())

    return sorted(out)


def find_first_trial(run_dir: Path):
    """
    Return first trial directory (typically 0000).

    Used by reporting layer to avoid generating
    thousands of identical trial report templates.
    """

    trials = find_trials(run_dir)

    if not trials:
        return None

    return sorted(trials)[0]


# =========================================================
# Metrics / Status
# =========================================================
def has_metrics(trial_dir: Path):
    """
    Return True if trial contains metrics.json.
    """

    return (Path(trial_dir) / "metrics.json").exists()


def summarize_run(run_dir: Path):
    """
    Summarize run completion status.
    """

    trial_dirs = find_trials(run_dir)

    total = len(trial_dirs)

    completed = sum(1 for td in trial_dirs if has_metrics(td))

    pending = total - completed

    return {
        "run_dir": Path(run_dir).resolve(),
        "total": total,
        "completed": completed,
        "pending": pending,
    }


# =========================================================
# Pending work discovery
# =========================================================
def find_pending_trials(results_root: Path):
    """
    Find all trials missing metrics.json.
    """

    out = []

    for run_dir in find_all_runs(results_root):
        for td in find_trials(run_dir):
            if not has_metrics(td):
                out.append(td.resolve())

    return sorted(out)
