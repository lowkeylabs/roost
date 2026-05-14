# src/owlroost/schema/plugins/derived.py

from __future__ import annotations

from owlroost.display.specs import DisplayProfile

from ..registry import FieldSpec

# =========================================================
# Helpers
# =========================================================


def _get_value(
    row,
    key,
):
    """
    Resolve a semantic value from a row.

    Lookup order:
        1. metrics
        2. inputs
        3. metadata
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

    val = row.get(
        "_meta",
        {},
    ).get(key)

    return val


def _safe_div(
    a,
    b,
):
    try:
        if b in (
            0,
            0.0,
            None,
        ):
            return None

        return a / b

    except Exception:
        return None


# =========================================================
# Derived Metrics
# =========================================================


def compute_trials_per_second(
    row,
):
    """
    Completed trials per wall-clock second.
    """

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


def compute_parallel_efficiency(
    row,
):
    """
    Effective parallel efficiency.

    Formula:

        completed_trials * mean_trial_seconds
        -------------------------------------
              run_wall_seconds
    """

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


def compute_trial_slowdown_factor(
    row,
):
    """
    Ratio of p90 trial duration
    to median trial duration.

    Higher values suggest:
    - contention
    - variability
    - scheduling instability
    """

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


def compute_worker_utilization(
    row,
):
    """
    Parallel efficiency normalized
    by workers_per_run.

    Ideal value approaches 1.0.
    """

    efficiency = compute_parallel_efficiency(
        row,
    )

    workers = _get_value(
        row,
        "roost_runtime.workers_per_run",
    )

    return _safe_div(
        efficiency,
        workers,
    )


def compute_trials_per_worker(
    row,
):
    """
    Completed trials per worker.
    """

    completed = _get_value(
        row,
        "run_execution.completed_trials",
    )

    workers = _get_value(
        row,
        "roost_runtime.workers_per_run",
    )

    return _safe_div(
        completed,
        workers,
    )


# =========================================================
# Plugin
# =========================================================


class DerivedMetricsPlugin:
    """
    Derived analytical metrics.

    These metrics are:
    - NOT persisted in metrics.json
    - computed dynamically
    - derived from inputs + metrics + metadata
    """

    def register(
        self,
        registry,
    ):
        # =================================================
        # Throughput
        # =================================================

        registry.register(
            FieldSpec(
                name="run_execution.trials_per_second",
                dtype=float,
                path=(
                    "run_execution",
                    "trials_per_second",
                ),
                source="derived",
                level="run",
                compute_fn=compute_trials_per_second,
                aggregates=[
                    "mean",
                    "median",
                    "min",
                    "max",
                    "p10",
                    "p90",
                ],
                description=("Completed trials per " "wall-clock second."),
                display_profiles={
                    "table": DisplayProfile(
                        label="Trials\nPer\nSecond",
                        fmt="float3",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Trials Per Second",
                        fmt="float3",
                        content_align="right",
                    ),
                },
            )
        )

        # =================================================
        # Parallel efficiency
        # =================================================

        registry.register(
            FieldSpec(
                name="run_execution.effective_parallelism",
                dtype=float,
                path=(
                    "run_execution",
                    "parallel_efficiency",
                ),
                source="derived",
                level="run",
                compute_fn=compute_parallel_efficiency,
                aggregates=[
                    "mean",
                    "median",
                    "min",
                    "max",
                ],
                description=("Effective parallel " "execution efficiency."),
                display_profiles={
                    "table": DisplayProfile(
                        label="Effective\nParallelism",
                        fmt="float3",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Effective Parallelism",
                        fmt="float3",
                        content_align="right",
                    ),
                },
            )
        )

        # =================================================
        # Worker utilization
        # =================================================

        registry.register(
            FieldSpec(
                name="run_execution.worker_utilization",
                dtype=float,
                path=(
                    "run_execution",
                    "worker_utilization",
                ),
                source="derived",
                level="run",
                compute_fn=compute_worker_utilization,
                aggregates=[
                    "mean",
                    "median",
                    "max",
                ],
                description=("Parallel efficiency " "normalized by workers."),
                display_profiles={
                    "table": DisplayProfile(
                        label="Worker\nUtil",
                        fmt="percent1",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Worker utilization",
                        fmt="percent1",
                        content_align="right",
                    ),
                },
            )
        )

        # =================================================
        # Trials per worker
        # =================================================

        registry.register(
            FieldSpec(
                name="run_execution.trials_per_worker",
                dtype=float,
                path=(
                    "run_execution",
                    "trials_per_worker",
                ),
                source="derived",
                level="run",
                compute_fn=compute_trials_per_worker,
                aggregates=[
                    "mean",
                    "median",
                ],
                description=("Completed trials per worker."),
                display_profiles={
                    "table": DisplayProfile(
                        label="Trials\nPer\nWorker",
                        fmt="float3",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Trials per worker (completed)",
                        fmt="float3",
                        content_align="right",
                    ),
                },
            )
        )

        # =================================================
        # Trial latency skew
        # =================================================

        registry.register(
            FieldSpec(
                name="run_timing.trial_latency_skew",
                dtype=float,
                path=(
                    "run_timing",
                    "trial_slowdown_factor",
                ),
                source="derived",
                level="run",
                compute_fn=compute_trial_slowdown_factor,
                aggregates=[
                    "mean",
                    "median",
                    "max",
                    "p90",
                ],
                description=("Ratio of p90 to median " "trial execution time."),
                display_profiles={
                    "table": DisplayProfile(
                        label="Latency\nSkew",
                        fmt="float3",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Latency skew",
                        fmt="float3",
                        content_align="right",
                    ),
                },
            )
        )
