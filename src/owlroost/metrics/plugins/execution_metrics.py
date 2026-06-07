# src/owlroost/metrics/plugins/execution_metrics.py
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

from ..specs import MetricSpec

# =========================================================
# Helpers
# =========================================================


def _get_value(row, key):
    """
    Resolve a semantic value from a row.

    Lookup order:

        1. _metrics
        2. _inputs
        3. _meta
    """

    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------

    val = row.get(
        "_metrics",
        {},
    ).get(key)

    if val is not None:
        return val

    # -----------------------------------------------------
    # Inputs
    # -----------------------------------------------------

    inputs = row.get(
        "_inputs",
        {},
    )

    current = inputs

    try:
        for part in key.split("."):
            current = current[part]

        return current

    except Exception:
        pass

    # -----------------------------------------------------
    # Metadata
    # -----------------------------------------------------

    return row.get(
        "_meta",
        {},
    ).get(key)


def _safe_div(a, b):
    try:
        if b in (0, 0.0, None):
            return None

        return a / b

    except Exception:
        return None


# =========================================================
# Compute Functions
# =========================================================


def compute_trials_per_second(row):
    completed = _get_value(
        row,
        "run_execution.completed_trials",
    )

    elapsed = _get_value(
        row,
        "run_timing.elapsed_seconds",
    )

    return _safe_div(
        completed,
        elapsed,
    )


def compute_parallel_efficiency(row):
    completed = _get_value(
        row,
        "run_execution.completed_trials",
    )

    mean_trial = _get_value(
        row,
        "timing.elapsed_seconds__mean",
    )

    wall = _get_value(
        row,
        "run_timing.elapsed_seconds",
    )

    try:
        numerator = completed * mean_trial

    except Exception:
        return None

    return _safe_div(
        numerator,
        wall,
    )


def compute_trial_slowdown_factor(row):
    p90 = _get_value(
        row,
        "timing.elapsed_seconds__p90",
    )

    median = _get_value(
        row,
        "timing.elapsed_seconds__median",
    )

    return _safe_div(
        p90,
        median,
    )


def compute_worker_utilization(row):
    efficiency = compute_parallel_efficiency(
        row,
    )

    workers = _get_value(
        row,
        "roost_settings.workers_per_run",
    )

    return _safe_div(
        efficiency,
        workers,
    )


def compute_trials_per_worker(row):
    completed = _get_value(
        row,
        "run_execution.completed_trials",
    )

    workers = _get_value(
        row,
        "roost_settings.workers_per_run",
    )

    return _safe_div(
        completed,
        workers,
    )


# =========================================================
# Plugin
# =========================================================


class ExecutionMetricsPlugin:
    """
    Derived runtime execution metrics.

    These metrics are:

        - NOT persisted
        - computed dynamically
        - derived from execution behavior
        - analytical runtime observations
    """

    def register(self, registry):
        # =================================================
        # Throughput
        # =================================================

        registry.register(
            MetricSpec(
                name="run_execution.trials_per_second",
                category="derived_metric",
                description=("Completed trials per wall-clock second."),
                owner="ROOST",
                semantic_domain="execution",
                value_origin="roost-computed",
                projection_kind="synthetic",
                analytic_kind="synthetic",
                materialization_level="run",
                dtype=float,
                compute_fn=compute_trials_per_second,
                aggregatable=True,
                default_aggregates=[
                    "mean",
                    "median",
                    "min",
                    "max",
                    "p10",
                    "p90",
                ],
            )
        )

        # =================================================
        # Parallel efficiency
        # =================================================

        registry.register(
            MetricSpec(
                name="run_execution.concurrency_equivalent",
                category="derived_metric",
                description=("Throughput-equivalent concurrency estimate."),
                owner="ROOST",
                semantic_domain="execution",
                value_origin="roost-computed",
                projection_kind="synthetic",
                analytic_kind="synthetic",
                materialization_level="run",
                dtype=float,
                compute_fn=compute_parallel_efficiency,
                aggregatable=True,
                default_aggregates=[
                    "mean",
                    "median",
                    "min",
                    "max",
                ],
            )
        )

        # =================================================
        # Worker utilization
        # =================================================

        registry.register(
            MetricSpec(
                name="run_execution.worker_utilization",
                category="derived_metric",
                description=("Parallel efficiency normalized by workers."),
                owner="ROOST",
                semantic_domain="execution",
                value_origin="roost-computed",
                projection_kind="synthetic",
                analytic_kind="synthetic",
                materialization_level="run",
                dtype=float,
                compute_fn=compute_worker_utilization,
                aggregatable=True,
                default_aggregates=[
                    "mean",
                    "median",
                    "max",
                ],
            )
        )

        # =================================================
        # Trials per worker
        # =================================================

        registry.register(
            MetricSpec(
                name="run_execution.trials_per_worker",
                category="derived_metric",
                description=("Completed trials per worker."),
                owner="ROOST",
                semantic_domain="execution",
                value_origin="roost-computed",
                projection_kind="synthetic",
                analytic_kind="synthetic",
                materialization_level="run",
                dtype=float,
                compute_fn=compute_trials_per_worker,
                aggregatable=True,
                default_aggregates=[
                    "mean",
                    "median",
                ],
            )
        )

        # =================================================
        # Trial latency skew
        # =================================================

        registry.register(
            MetricSpec(
                name="run_timing.trial_latency_skew",
                category="derived_metric",
                description=("Ratio of p90 to median trial execution time."),
                owner="ROOST",
                semantic_domain="execution",
                value_origin="roost-computed",
                projection_kind="synthetic",
                analytic_kind="synthetic",
                materialization_level="run",
                dtype=float,
                compute_fn=compute_trial_slowdown_factor,
                aggregatable=True,
                default_aggregates=[
                    "mean",
                    "median",
                    "max",
                    "p90",
                ],
            )
        )
