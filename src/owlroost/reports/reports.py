# src/owlroost/reports/reports.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

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

import yaml

from owlroost.display.discovery import (
    find_first_trial,
    find_runs,
    find_sessions,
)


# =========================================================
# Low-level helpers
# =========================================================
def write_metadata(
    path: Path,
    data: dict,
):
    """
    Write YAML metadata file.
    """

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(path, "w") as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
        )


def copy_template(
    template_path: Path,
    target_path: Path,
):
    """
    Copy template file if source exists.
    """

    if not template_path.exists():
        return

    target_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        template_path,
        target_path,
    )


# =========================================================
# Artifact management
# =========================================================
def ensure_report_artifacts(
    target_dir: Path,
    level: str,
    templates_root: Path,
    meta_vars: dict,
):
    """
    Ensure metadata + qmd artifacts exist.
    """

    target_dir = target_dir.resolve()

    metadata = {
        "level": level,
        "paths": {
            **{k: str(Path(v).resolve()) for k, v in meta_vars.items()},
            "template_dir": str(templates_root.resolve()),
        },
    }

    # ----------------------------------------
    # Metadata
    # ----------------------------------------
    metadata_path = target_dir / "_metadata.yml"

    write_metadata(
        metadata_path,
        metadata,
    )

    # ----------------------------------------
    # QMD
    # ----------------------------------------
    template_qmd = templates_root / "reports" / level / f"{level}.qmd"

    target_qmd = target_dir / f"{level}.qmd"

    copy_template(
        template_qmd,
        target_qmd,
    )


def check_report_artifacts(
    target_dir: Path,
    level: str,
):
    """
    Return list of missing artifacts.
    """

    issues = []

    if not (target_dir / "_metadata.yml").exists():
        issues.append("missing _metadata.yml")

    if not (target_dir / f"{level}.qmd").exists():
        issues.append(f"missing {level}.qmd")

    return issues


# =========================================================
# Template initialization
# =========================================================
def initialize_templates(
    source_dir: Path,
    destination_dir: Path,
    project_root: Path,
    force=False,
):
    """
    Initialize reporting template tree.
    """

    source_dir = Path(source_dir).resolve()

    destination_dir = Path(destination_dir).resolve()

    project_root = Path(project_root).resolve()

    if not source_dir.exists():
        raise FileNotFoundError(f"Source templates not found: {source_dir}")

    if not source_dir.is_dir():
        raise NotADirectoryError(f"Source must be a directory: {source_dir}")

    required = [
        "case",
        "session",
        "run",
        "trial",
    ]

    missing = [d for d in required if not (source_dir / d).exists()]

    if missing:
        raise RuntimeError(f"Template source missing required folders: {', '.join(missing)}")

    # ----------------------------------------
    # Replace destination
    # ----------------------------------------
    if destination_dir.exists():
        if not force:
            raise FileExistsError("Destination templates already exists")

        shutil.rmtree(destination_dir)

    shutil.copytree(
        source_dir,
        destination_dir,
    )

    # ----------------------------------------
    # Promote root files
    # ----------------------------------------
    promote_files = [
        "_quarto.yml",
        "_variables.yml",
    ]

    moved = []

    for fname in promote_files:
        src_file = destination_dir / fname

        dst_file = project_root / fname

        if not src_file.exists():
            continue

        if dst_file.exists():
            if not force:
                continue

            dst_file.unlink()

        shutil.move(
            str(src_file),
            str(dst_file),
        )

        moved.append(fname)

    return {
        "templates_dir": destination_dir,
        "moved_files": moved,
    }


# =========================================================
# Template status
# =========================================================
def resolve_template_status(
    templates_dir: Path,
):
    """
    Check reporting template completeness.
    """

    required = [
        "case",
        "session",
        "run",
        "trial",
    ]

    status = {
        "exists": templates_dir.exists(),
        "missing_subdirs": [],
    }

    if status["exists"]:
        for sub in required:
            if not (templates_dir / sub).exists():
                status["missing_subdirs"].append(sub)

    return status


# =========================================================
# Sync
# =========================================================
def sync_reports(
    results_dir: Path,
    templates_dir: Path,
):
    """
    Generate report artifacts across
    results tree.
    """

    results_dir = Path(results_dir).resolve()

    templates_dir = Path(templates_dir).resolve()

    case_seen = set()

    for exp_dir in find_sessions(results_dir):
        exp_dir = Path(exp_dir).resolve()

        # results/<case>/<date>/<time>
        case_dir = exp_dir.parent.parent

        # ------------------------------------
        # CASE
        # ------------------------------------
        if case_dir not in case_seen:
            ensure_report_artifacts(
                case_dir,
                "case",
                templates_dir,
                {
                    "case_dir": case_dir,
                },
            )

            case_seen.add(case_dir)

        # ------------------------------------
        # session
        # ------------------------------------
        ensure_report_artifacts(
            exp_dir,
            "session",
            templates_dir,
            {
                "session_dir": exp_dir,
                "case_dir": case_dir,
            },
        )

        # ------------------------------------
        # RUNS
        # ------------------------------------
        for run_dir in find_runs(exp_dir):
            run_dir = Path(run_dir).resolve()

            ensure_report_artifacts(
                run_dir,
                "run",
                templates_dir,
                {
                    "run_dir": run_dir,
                    "session_dir": exp_dir,
                    "case_dir": case_dir,
                },
            )

            # --------------------------------
            # FIRST TRIAL ONLY
            # --------------------------------
            trial_dir = find_first_trial(run_dir)

            if trial_dir is not None:
                ensure_report_artifacts(
                    trial_dir,
                    "trial",
                    templates_dir,
                    {
                        "trial_dir": trial_dir,
                        "run_dir": run_dir,
                        "session_dir": exp_dir,
                        "case_dir": case_dir,
                    },
                )


# =========================================================
# Diagnostics
# =========================================================
def collect_report_diagnostics(
    results_dir: Path,
    templates_dir: Path,
):
    """
    Collect reporting synchronization status.
    """

    results_dir = Path(results_dir).resolve()

    templates_dir = Path(templates_dir).resolve()

    counts = {
        "case": {
            "total": 0,
            "missing": 0,
        },
        "session": {
            "total": 0,
            "missing": 0,
        },
        "run": {
            "total": 0,
            "missing": 0,
        },
        "trial": {
            "total": 0,
            "missing": 0,
        },
    }

    def check_and_count(
        path: Path,
        level: str,
    ):
        issues = check_report_artifacts(
            path,
            level,
        )

        counts[level]["total"] += 1

        if issues:
            counts[level]["missing"] += 1

    case_seen = set()

    for exp_dir in find_sessions(results_dir):
        exp_dir = Path(exp_dir).resolve()

        case_dir = exp_dir.parent.parent

        # ------------------------------------
        # CASE
        # ------------------------------------
        if case_dir not in case_seen:
            check_and_count(
                case_dir,
                "case",
            )

            case_seen.add(case_dir)

        # ------------------------------------
        # session
        # ------------------------------------
        check_and_count(
            exp_dir,
            "session",
        )

        # ------------------------------------
        # RUNS
        # ------------------------------------
        for run_dir in find_runs(exp_dir):
            run_dir = Path(run_dir).resolve()

            check_and_count(
                run_dir,
                "run",
            )

            # --------------------------------
            # FIRST TRIAL ONLY
            # --------------------------------
            trial_dir = find_first_trial(run_dir)

            if trial_dir is not None:
                check_and_count(
                    trial_dir,
                    "trial",
                )

    template_status = resolve_template_status(templates_dir)

    total_missing = sum(v["missing"] for v in counts.values())

    template_problem = not template_status["exists"] or len(template_status["missing_subdirs"]) > 0

    return {
        "template_status": template_status,
        "counts": counts,
        "total_missing": total_missing,
        "healthy": (total_missing == 0 and not template_problem),
    }
