# src/owlroost/display/loaders.py
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

import json
import tomllib
from pathlib import Path

import yaml

from owlroost.core.hfp import summarize_hfp
from owlroost.metrics.aggregation.service import (
    aggregate_rows,
)
from owlroost.metrics.materializers import (
    materialize_row_metrics,
)

from .discovery.cases import (
    find_case_files,
)
from .discovery.results_tree import (
    find_all_runs,
    find_trials,
    summarize_run,
)

# =========================================================
# Helpers
# =========================================================


def extract_run_id(
    run_dir: Path,
):
    """
    run_0 -> 0
    """

    name = run_dir.name

    if not name.startswith("run_"):
        return None

    try:
        return int(name.split("_")[1])

    except Exception:
        return None


def extract_trial_id(
    trial_dir: Path,
):
    """
    0007 -> 7
    """

    try:
        return int(trial_dir.name)

    except Exception:
        return None


def extract_session_key(
    run_dir: Path,
):
    """
    results/<case>/<date>/<time>/run_X

    returns:
        (<case>, <date>, <time>)
    """

    parts = run_dir.parts

    if len(parts) < 4:
        return None

    return (
        parts[-4],
        parts[-3],
        parts[-2],
    )


def validate_results_path(
    path: Path,
    results_root: Path,
):
    """
    Ensure path is contained inside results_root.
    """

    path = path.resolve()

    results_root = results_root.resolve()

    try:
        path.relative_to(results_root)

    except ValueError as err:
        raise ValueError(f"Unsafe path outside results root: {path}") from err

    return path


# =========================================================
# Path Helpers
# =========================================================


def build_result_paths(
    run_dir: Path,
    results_root: Path,
):
    """
    Build canonical filesystem paths for a run.

    Expected structure:

        results/<case>/<date>/<time>/run_X

    Where:
        - <case>  = case directory
        - <date>  = session date directory
        - <time>  = session directory
        - run_X   = run directory

    Returns:
        {
            "results_root": ...,
            "case_dir": ...,
            "date_dir": ...,
            "session_dir": ...,
            "run_dir": ...,
            "session_date": ...,
            "session_time": ...,
        }
    """

    # =====================================================
    # Canonicalize + validate
    # =====================================================

    results_root = Path(results_root).resolve()

    run_dir = validate_results_path(
        Path(run_dir).resolve(),
        results_root,
    )

    # =====================================================
    # Hierarchy
    # =====================================================

    session_dir = validate_results_path(
        run_dir.parent.resolve(),
        results_root,
    )

    date_dir = validate_results_path(
        session_dir.parent.resolve(),
        results_root,
    )

    case_dir = validate_results_path(
        date_dir.parent.resolve(),
        results_root,
    )

    # =====================================================
    # Derived labels
    # =====================================================

    session_date = date_dir.name
    session_time = session_dir.name
    session_timestamp = f"{session_date}T{session_time}"
    # =====================================================
    # Return structure
    # =====================================================

    return {
        "results_root": results_root,
        "case_dir": case_dir,
        "date_dir": date_dir,
        "session_dir": session_dir,
        "run_dir": run_dir,
        "session_date": session_date,
        "session_time": session_time,
        "session_timestamp": session_timestamp,
    }


# =========================================================
# Metric Normalization
# =========================================================


def flatten_dict(
    d,
    prefix="",
):
    """
    Flatten nested dictionaries into dotted-path keys.

    Example
    -------
        {
            "financial": {
                "spending": {
                    "today": 123
                }
            }
        }

    becomes:

        {
            "financial.spending.today": 123
        }
    """

    out = {}

    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k

        if isinstance(
            v,
            dict,
        ):
            out.update(
                flatten_dict(
                    v,
                    key,
                )
            )

        else:
            out[key] = v

    return out


# =========================================================
# Case Loader
# =========================================================


def _load_case_file(
    path: Path,
    metrics_registry,
    *,
    load_hfp=True,
):
    """
    Load a single TOML case file into row format.

    Parameters
    ----------
    load_hfp
        If True, load summarized HFP metadata.

        If False, skip workbook loading entirely.
    """

    path = Path(path)

    # =====================================================
    # Load TOML
    # =====================================================

    try:
        content = tomllib.loads(path.read_text())

    except Exception:
        return None

    # =====================================================
    # Case name
    # =====================================================

    case_name = content.get(
        "case_name",
        path.stem,
    )

    # =====================================================
    # HFP summary
    # =====================================================

    if load_hfp:
        hfp_summary = summarize_hfp(
            path,
            content,
        )

    else:
        hfp_summary = {
            "has_hfp": False,
            "hfp_status": "disabled",
        }

    # =====================================================
    # Case row
    # =====================================================

    resolved_path = path.resolve()

    row = {
        "_path": resolved_path,
        "_paths": {
            "case_file": resolved_path,
        },
        "_case_name": case_name,
        "_inputs": content,
        "_metrics": {},
        "_hfp": hfp_summary,
        "_meta": {
            "level": "case",
        },
    }

    materialize_row_metrics(
        row,
        metrics_registry,
    )

    return row


# =========================================================
# Trial Metrics
# =========================================================


def _load_trial_metrics(
    trial_dir: Path,
    *,
    case_id,
    session_id,
    run_id,
    results_root,
):
    """
    Load metrics.json from trial directory.

    Trial rows are canonical aggregation inputs.
    """

    metrics_file = Path(trial_dir) / "metrics.json"

    if not metrics_file.exists():
        return None

    try:
        metrics = json.loads(metrics_file.read_text())

    except Exception:
        return None

    resolved_trial_dir = Path(trial_dir).resolve()
    run_dir = resolved_trial_dir.parent.parent
    trial_id = extract_trial_id(trial_dir)

    return {
        "_path": resolved_trial_dir,
        "_paths": {
            **build_result_paths(run_dir, results_root),
            "trial_dir": resolved_trial_dir,
        },
        "_inputs": {},
        "_metrics": flatten_dict(metrics),
        "_meta": {
            "level": "trial",
            "case_id": case_id,
            "session_id": session_id,
            "run_id": run_id,
            "trial_id": trial_id,
        },
    }


# =========================================================
# Run timing
# =========================================================


def _load_run_timing(
    run_dir: Path,
):
    """
    Load run_timing.json.
    """

    timing_file = Path(run_dir) / "run_timing.json"

    if not timing_file.exists():
        return {}

    try:
        timing = json.loads(timing_file.read_text())

    except Exception:
        return {}

    return flatten_dict(timing)


# =========================================================
# Run Loader
# =========================================================


def _load_run_dir(
    path: Path,
    metrics_registry,
    *,
    case_id,
    session_id,
    run_id,
    results_root,
):
    """
    Load a single run directory.

    Responsibilities:
        - load run.toml
        - summarize completion
        - aggregate trial metrics
    """

    path = Path(path)

    run_toml = path / "run.toml"

    if not run_toml.exists():
        return None

    # =====================================================
    # Load TOML
    # =====================================================

    try:
        content = tomllib.loads(run_toml.read_text())
        task_overrides = load_hydra_overrides(path)

    except Exception:
        return None

    try:
        hfp_summary = summarize_hfp(
            run_toml,
            content,
        )
    except Exception:
        return None

    # =====================================================
    # Completion Summary
    # =====================================================

    summary = summarize_run(path)

    total = summary["total"]

    completed = summary["completed"]

    pending = summary["pending"]

    completion_rate = completed / total if total > 0 else 0.0

    # =====================================================
    # Load Trial Rows
    # =====================================================

    trial_rows = []

    for trial_dir in find_trials(path):
        row = _load_trial_metrics(
            trial_dir,
            case_id=case_id,
            session_id=session_id,
            run_id=run_id,
            results_root=results_root,
        )

        if row is not None:
            trial_rows.append(row)

    # =====================================================
    # Aggregate Trial Metrics
    # =====================================================

    agg_metrics = {}

    if trial_rows:
        agg_metrics = aggregate_rows(
            rows=trial_rows,
            metrics_registry=metrics_registry,
        )

    # =====================================================
    # Run timing metrics
    # =====================================================

    run_timing_metrics = _load_run_timing(path)

    # =====================================================
    # Dataset Row
    # =====================================================

    resolved_run_dir = path.resolve()

    result_paths = build_result_paths(
        resolved_run_dir,
        results_root,
    )
    result_paths["case_file"] = run_toml.resolve()

    row = {
        "_path": resolved_run_dir,
        "_paths": result_paths,
        "_inputs": content,
        "_metrics": {
            # -------------------------------------------------
            # Run completion
            # -------------------------------------------------
            "trial.total": total,
            "trial.completed": completed,
            "trial.pending": pending,
            "trial.completion_rate": completion_rate,
            # -------------------------------------------------
            # Aggregated metrics
            # -------------------------------------------------
            **agg_metrics,
            **run_timing_metrics,
        },
        "_hfp": hfp_summary,
        "_meta": {
            "level": "run",
            "trial_count": total,
            "case_id": case_id,
            "session_id": session_id,
            "run_id": run_id,
            "task_overrides": task_overrides,
            "session.timestamp": (result_paths["session_timestamp"]),
        },
    }

    materialize_row_metrics(
        row,
        metrics_registry,
    )

    return row


# =========================================================
# Public Loaders
# =========================================================


def load_hydra_overrides(
    run_dir: Path,
):
    """
    Load hydra_overrides.yaml from run directory.
    """

    path = Path(run_dir) / "hydra_overrides.yaml"

    if not path.exists():
        return []

    try:
        data = yaml.safe_load(path.read_text())

    except Exception:
        return []

    return data.get(
        "task_overrides",
        [],
    )


def load_case_rows(
    source: Path | str = ".",
    *,
    metrics_registry,
    load_hfp=True,
):
    """
    Load case rows from:

        - directory of TOML case files
        - YAML list of TOML paths

    Parameters
    ----------
    load_hfp
        If True, load summarized HFP metadata.

        If False, skip workbook loading entirely.
    """

    source = Path(source)

    # =====================================================
    # Directory → discover TOML files
    # =====================================================

    if source.is_dir():
        rows = []

        for path in find_case_files(source):
            row = _load_case_file(
                path,
                metrics_registry,
                load_hfp=load_hfp,
            )

            if row is not None:
                rows.append(row)

        for idx, row in enumerate(rows):
            row.setdefault("_meta", {})
            row["_meta"]["case_id"] = idx

        return rows

    # =====================================================
    # YAML → explicit TOML file list
    # =====================================================

    if source.suffix in (
        ".yml",
        ".yaml",
    ):
        data = yaml.safe_load(source.read_text())

        rows = []

        for p in data:
            row = _load_case_file(
                Path(p),
                metrics_registry,
                load_hfp=load_hfp,
            )

            if row is not None:
                rows.append(row)

        for idx, row in enumerate(rows):
            row.setdefault("_meta", {})
            row["_meta"]["case_id"] = idx

        return rows

    # =====================================================
    # Unsupported source
    # =====================================================

    raise ValueError(f"Unsupported source: {source}")


# =========================================================
# Run Datasets
# =========================================================


def load_run_rows(
    metrics_registry,
    results_root="results",
):
    """
    Load run dataset from results tree.

    Each row contains:

        - run configuration (_inputs)
        - aggregated metrics (_metrics)
        - runtime metadata (_meta)
    """

    results_root = Path(results_root).resolve()

    # =====================================================
    # Discover Runs
    # =====================================================

    run_dirs = sorted(find_all_runs(results_root))

    # =====================================================
    # Build Case ID Map
    # =====================================================

    case_names = sorted(
        {extract_session_key(r)[0] for r in run_dirs if extract_session_key(r) is not None}
    )

    case_id_map = {name: idx for idx, name in enumerate(case_names)}

    # =====================================================
    # Build session ID Map
    # =====================================================

    sessions_by_case = {}

    for run_dir in run_dirs:
        session_key = extract_session_key(run_dir)

        if session_key is None:
            continue

        case_name = session_key[0]

        sessions_by_case.setdefault(case_name, set()).add(session_key)

    session_id_map = {}

    for _case_name, keys in sessions_by_case.items():
        for idx, key in enumerate(sorted(keys)):
            session_id_map[key] = idx

    # =====================================================
    # Load Rows
    # =====================================================

    rows = []

    for run_dir in run_dirs:
        session_key = extract_session_key(run_dir)

        if session_key is None:
            continue

        case_name = session_key[0]

        row = _load_run_dir(
            run_dir,
            metrics_registry=metrics_registry,
            case_id=case_id_map[case_name],
            session_id=session_id_map[session_key],
            run_id=extract_run_id(run_dir),
            results_root=results_root,
        )

        if row is not None:
            rows.append(row)

    return rows


def load_cases():
    pass


def load_runs():
    pass


def load_trial_as_row(
    source=".",
    *,
    metrics_registry,
):
    """
    Load a single trial directory as a
    display-compatible row.

    Expected contents
    -----------------
    trial.toml
        Materialized trial inputs.

    metrics.json
        Trial metrics.

    trial_meta.yaml (optional)
        Trial metadata.

    _metadata.yml (optional)
        Additional metadata.

    Returns
    -------
    dict
        Canonical display row.
    """

    source = Path(source).resolve()

    # =====================================================
    # Inputs
    # =====================================================

    inputs = {}

    trial_toml = source / "trial.toml"

    if trial_toml.exists():
        try:
            inputs = tomllib.loads(trial_toml.read_text())
        except Exception:
            pass

    # =====================================================
    # Metrics
    # =====================================================

    metrics = {}

    metrics_file = source / "metrics.json"

    if metrics_file.exists():
        try:
            metrics = flatten_dict(json.loads(metrics_file.read_text()))
        except Exception:
            pass

    # =====================================================
    # Metadata
    # =====================================================

    meta = {
        "level": "trial",
    }

    trial_meta = source / "trial_meta.yaml"

    if trial_meta.exists():
        try:
            meta.update(yaml.safe_load(trial_meta.read_text()) or {})
        except Exception:
            pass

    metadata_file = source / "_metadata.yml"

    if metadata_file.exists():
        try:
            meta.update(yaml.safe_load(metadata_file.read_text()) or {})
        except Exception:
            pass

    # =====================================================
    # Paths
    # =====================================================

    paths = {
        "trial_dir": source,
    }

    # =====================================================
    # Row
    # =====================================================

    hfp_summary = summarize_hfp(
        trial_toml,
        inputs,
    )

    row = {
        "_path": source,
        "_paths": paths,
        "_case_name": inputs.get(
            "case_name",
            source.name,
        ),
        "_inputs": inputs,
        "_metrics": metrics,
        "_hfp": hfp_summary,
        "_meta": meta,
    }

    materialize_row_metrics(
        row,
        metrics_registry,
    )

    return [row]
