# src/owlroost/display/loaders.py

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import yaml

from owlroost.metrics.aggregation.service import (
    aggregate_dataset,
)

from .dataset import Dataset
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


def _load_case_file(
    path: Path,
):
    """
    Load a single TOML case file into dataset row format.
    """

    path = Path(path)

    try:
        content = tomllib.loads(path.read_text())

    except Exception:
        return None

    return {
        "_path": path.resolve(),
        "_inputs": content,
        "_metrics": {},
        "_meta": {
            "level": "case",
        },
    }


# =========================================================
# Trial Metrics
# =========================================================


def _load_trial_metrics(
    trial_dir: Path,
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

    return {
        "_path": Path(trial_dir).resolve(),
        "_inputs": {},
        "_metrics": flatten_dict(metrics),
        "_meta": {
            "level": "trial",
        },
    }


# =========================================================
# Run Loader
# =========================================================


def _load_run_dir(
    path: Path,
    metrics_registry,
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
    # Load Trial Dataset
    # =====================================================

    trial_rows = []

    for trial_dir in find_trials(path):
        row = _load_trial_metrics(trial_dir)

        if row is not None:
            trial_rows.append(row)

    trial_dataset = Dataset(
        trial_rows,
        level="trial",
    )

    # =====================================================
    # Aggregate Trial Metrics
    # =====================================================

    agg_metrics = {}

    if trial_rows:
        agg_metrics = aggregate_dataset(
            dataset=trial_dataset,
            metrics_registry=metrics_registry,
        )

    # =====================================================
    # Dataset Row
    # =====================================================

    return {
        "_path": path.resolve(),
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
        },
        "_meta": {
            "level": "run",
            "trial_count": total,
        },
    }


# =========================================================
# Public Loaders
# =========================================================


def load_cases(
    source=".",
):
    """
    Load case dataset from:

        - directory of TOML case files
        - YAML list of TOML paths
    """

    source = Path(source)

    # =====================================================
    # Directory → discover TOML files
    # =====================================================

    if source.is_dir():
        rows = []

        for path in find_case_files(source):
            row = _load_case_file(path)

            if row is not None:
                rows.append(row)

        return Dataset(
            rows,
            level="case",
        )

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
            row = _load_case_file(Path(p))

            if row is not None:
                rows.append(row)

        return Dataset(
            rows,
            level="case",
        )

    raise ValueError(f"Unsupported source: {source}")


# =========================================================
# Run Datasets
# =========================================================


def load_runs(
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

    rows = []

    for run_dir in find_all_runs(Path(results_root)):
        row = _load_run_dir(
            run_dir,
            metrics_registry=metrics_registry,
        )

        if row is not None:
            rows.append(row)

    return Dataset(
        rows,
        level="run",
    )
