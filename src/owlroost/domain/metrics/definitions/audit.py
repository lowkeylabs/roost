# domain/metrics/definitions/audit.py

from ..metric_definitions import wrap_value_fn
from ..metric_registry import register_metric
from ..metric_spec import MetricSpec

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------


def _trials(r):
    return (r.get("_ctx") or {}).get("trial_rows") or []


def _trial_total(r):
    trials = _trials(r)
    return len(trials)


def _is_solved(t):
    return (t.get("status") or "").lower() == "solved"


def _is_failed(t):
    return (t.get("status") or "").lower() in ("failed", "crashed", "timeout")


def _cat(t):
    return t.get("failure_category") or "unknown"


def _sub(t):
    return t.get("failure_subtype")


# ---------------------------------------------------------
# TIMEOUT COUNT
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="timeout_cnt",
        label="Timeouts",
        dtype=int,
        compute_level="run",
        compute_fn=lambda r: sum(1 for t in _trials(r) if _cat(t) == "timeout"),
        description="Number of trials that timed out.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{v} timeouts" if v else "-"),
    )
)


# ---------------------------------------------------------
# ERROR COUNT (EXCLUDES TIMEOUTS)  🔁 RENAMED
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="error_cnt",
        label="Errors",
        dtype=int,
        compute_level="run",
        compute_fn=lambda r: sum(1 for t in _trials(r) if _is_failed(t) and _cat(t) != "timeout"),
        description="Number of trials that errored (excluding timeouts).",
        value_series_fn=wrap_value_fn(lambda v, _: f"{v} errors" if v else "-"),
    )
)


# ---------------------------------------------------------
# TOTAL ERROR COUNT (INCLUDES TIMEOUTS)
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="error_total",
        label="Total\nErrors",
        dtype=int,
        compute_level="run",
        compute_fn=lambda r: sum(1 for t in _trials(r) if _is_failed(t)),
        description="Total errored trials (including timeouts).",
    )
)


# ---------------------------------------------------------
# SOLVED COUNT
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="solved_cnt",
        label="Solved",
        dtype=int,
        compute_level="run",
        compute_fn=lambda r: sum(1 for t in _trials(r) if _is_solved(t)),
        description="Number of trials successfully solved.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{v} solved" if v else "-"),
    )
)


# ---------------------------------------------------------
# COMPLETENESS (FIXED)
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="trial_completeness",
        label="Complete",
        dtype=float,
        compute_level="run",
        fmt="percent",
        compute_fn=lambda r: (
            sum(1 for t in _trials(r) if _is_solved(t)) / len(_trials(r)) if _trials(r) else 0
        ),
        description="Fraction of expected trials that completed.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{v:.0%} complete"),
    )
)


# ---------------------------------------------------------
# TIMEOUT RATE
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="timeout_rate",
        label="Timeout %",
        dtype=float,
        fmt="percent",
        compute_level="run",
        compute_fn=lambda r: (
            sum(1 for t in _trials(r) if _cat(t) == "timeout") / _trial_total(r)
            if _trial_total(r)
            else 0
        ),
        description="Fraction of trials that timed out.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{v:.1%} timeouts"),
    )
)


# ---------------------------------------------------------
# ERROR RATE (EXCLUDES TIMEOUTS)  🔁 RENAMED
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="error_rate",
        label="Error %",
        dtype=float,
        fmt="percent",
        compute_level="run",
        compute_fn=lambda r: (
            sum(1 for t in _trials(r) if _is_failed(t) and _cat(t) != "timeout") / _trial_total(r)
            if _trial_total(r)
            else 0
        ),
        description="Fraction of trials that errored (excluding timeouts).",
        value_series_fn=wrap_value_fn(lambda v, _: f"{v:.1%} errors"),
    )
)


# ---------------------------------------------------------
# FAILURE BREAKDOWN (WITH SUBTYPE)
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="failure_breakdown",
        label="Failure Breakdown",
        dtype=str,
        compute_level="run",
        compute_fn=lambda r: _failure_breakdown(r),
        description="Counts of failure categories (with subtype).",
    )
)


def _failure_breakdown(r):
    counts = {}

    for t in _trials(r):
        if _is_failed(t):
            cat = _cat(t)
            sub = _sub(t)

            key = f"{cat}:{sub}" if sub else cat
            counts[key] = counts.get(key, 0) + 1

    if not counts:
        return "-"

    parts = [f"{k}:{v}" for k, v in sorted(counts.items())]
    return ", ".join(parts)


# ---------------------------------------------------------
# FLAGS
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="audit_flags",
        label="Flags",
        dtype=str,
        compute_level="run",
        compute_fn=lambda r: _audit_flags(r),
        description="Diagnostic flags for run health.",
    )
)


def _audit_flags(r):
    flags = []

    total = _trial_total(r)
    actual = len(_trials(r))

    if total and actual < total:
        flags.append("INCOMPLETE")

    timeout_cnt = sum(1 for t in _trials(r) if _cat(t) == "timeout")

    if total and timeout_cnt / total > 0.1:
        flags.append("TIMEOUT_HEAVY")

    error_cnt = sum(1 for t in _trials(r) if _is_failed(t) and _cat(t) != "timeout")

    if total and error_cnt / total > 0.1:
        flags.append("ERROR_HEAVY")

    return ", ".join(flags) if flags else "-"


# ---------------------------------------------------------
# BAD TRIALS (WITH CATEGORY)
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="bad_trials",
        label="Bad Trials",
        dtype=str,
        compute_level="run",
        compute_fn=lambda r: _bad_trials(r),
        description="List of trial IDs that failed or timed out.",
    )
)


def _bad_trials(r):
    bad = [f"{t.get('trial_id')}({_cat(t)})" for t in _trials(r) if not _is_solved(t)]

    if not bad:
        return "-"

    preview = bad[:5]
    more = len(bad) - len(preview)

    return f"{', '.join(preview)} (+{more})" if more > 0 else ", ".join(preview)


register_metric(
    MetricSpec(
        key="worker_timeout",
        label="Timeout",
        dtype=int,
        compute_level="run",
        is_invariant=True,
        compute_fn=lambda r: ((r.get("_inputs") or {}).get("runtime", {}).get("worker_timeout")),
        description="Configured worker timeout (seconds).",
        value_series_fn=wrap_value_fn(lambda v, *_: f"{v}s" if isinstance(v, int) else (v or "-")),
        display_row_fn=lambda v, *_: (
            f"{v}s" if isinstance(v, int) else (v if isinstance(v, str) else "-")
        ),
    )
)

register_metric(
    MetricSpec(
        key="solver",
        label="Solver",
        dtype=int,
        compute_level="run",
        # is_invariant=True,
        compute_fn=lambda r: (
            (r.get("_inputs") or {}).get("solver_options", {}).get("solver", "default")
        ),
        description="Selected solver for the run.",
        value_series_fn=wrap_value_fn(lambda v, *_: f"{v}s" if isinstance(v, int) else (v or "-")),
        display_row_fn=lambda v, *_: (
            f"{v}s" if isinstance(v, int) else (v if isinstance(v, str) else "-")
        ),
    )
)

register_metric(
    MetricSpec(
        key="trial_jobs",
        label="Trial\nJobs",
        dtype=int,
        compute_level="run",
        # is_invariant=True,
        compute_fn=lambda r: ((r.get("_inputs") or {}).get("runtime", {}).get("trial_jobs")),
        description="Parallel Trial jobs configured for this run.",
        value_series_fn=wrap_value_fn(lambda v, *_: f"{v}" if isinstance(v, int) else (v or "-")),
        display_row_fn=lambda v, *_: (
            f"{v}" if isinstance(v, int) else (v if isinstance(v, str) else "-")
        ),
    )
)


# ---------------------------------------------------------
# Elapsed time
# ---------------------------------------------------------


def _elapsed_seconds(r):
    start = r.get("started_at")
    end = r.get("finished_at")

    if isinstance(start, (int, float)) and isinstance(end, (int, float)):
        return end - start

    return (
        r.get("elapsed_seconds")
        or r.get("elapsed")
        or (r.get("timing") or {}).get("elapsed_seconds")
    )


register_metric(
    MetricSpec(
        key="elapsed_seconds",
        label="Time (s)",
        fmt="float2",
        dtype=float,
        compute_level="trial",
        compute_fn=_elapsed_seconds,
        aggregates=["median", "mean", "std", "p10", "p90", "p99", "min", "max"],
        description="Elapsed solve time per trial (seconds).",
    )
)

# ---------------------------------------------------------
# Start time (epoch → formatted later)
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="started_at",
        label="Start\nTime",
        fmt="time_hms",
        dtype=float,
        compute_level="trial",
        compute_fn=lambda r: r.get("started_at"),
        aggregates=[],  # ❗ do NOT aggregate timestamps
        description="Trial start time (wall-clock).",
    )
)

# ---------------------------------------------------------
# Finish time
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="finished_at",
        label="Finish\nTime",
        fmt="time_hms",
        dtype=float,
        compute_level="trial",
        compute_fn=lambda r: r.get("finished_at"),
        aggregates=[],  # ❗ do NOT aggregate timestamps
        description="Trial completion time (wall-clock).",
    )
)

# ---------------------------------------------------------
# MAX TIME (EXCLUDING TIMEOUTS)
# ---------------------------------------------------------


def _elapsed_non_timeout(r):
    vals = []

    for t in (r.get("_ctx") or {}).get("trial_rows") or []:
        if (t.get("failure_category") or "") == "timeout":
            continue

        v = t.get("elapsed_seconds")

        if isinstance(v, (int, float)):
            vals.append(v)

    return max(vals) if vals else None


register_metric(
    MetricSpec(
        key="elapsed_max_nt",
        label="Max Time NT (s)",
        dtype=float,
        compute_level="run",
        fmt="float2",
        compute_fn=_elapsed_non_timeout,
        description="Maximum trial elapsed time excluding timeouts.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"{v:.1f}s" if isinstance(v, (int, float)) else "-"
        ),
    )
)

# ---------------------------------------------------------
# TRIAL-LEVEL STATUS / FAILURE METRICS
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="status_trial",
        label="Status",
        dtype=str,
        compute_level="trial",
        compute_fn=lambda r: r.get("status") or "-",
        description="Execution status of the trial (solved, failed, timeout, etc).",
    )
)

register_metric(
    MetricSpec(
        key="failure_category",
        label="Failure",
        dtype=str,
        compute_level="trial",
        compute_fn=lambda r: r.get("failure_category") or "-",
        description="Failure category for the trial (timeout, infeasible, etc).",
    )
)

register_metric(
    MetricSpec(
        key="failure_subtype",
        label="Subtype",
        dtype=str,
        compute_level="trial",
        compute_fn=lambda r: r.get("failure_subtype") or "-",
        description="Detailed failure subtype if available.",
    )
)

register_metric(
    MetricSpec(
        key="failure_detail",
        label="Failure\nDetail",
        dtype=str,
        compute_level="trial",
        compute_fn=lambda r: r.get("failure_detail") or "-",
        description="Failure detail if available (e.g. solver message).",
    )
)

# ---------------------------------------------------------
# TRIAL FLAGS (FOR FILTERING)
# ---------------------------------------------------------

# ---------------------------------------------------------
# Trial outcome flags
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="timeout",
        label="Timeouts",
        dtype=int,
        compute_level="trial",
        aggregates=["sum", "pct"],
        compute_fn=lambda r: 1 if (r.get("failure_category") or "") == "timeout" else 0,
        description="1 if trial timed out, else 0.",
    )
)

register_metric(
    MetricSpec(
        key="error",
        label="Errors",
        dtype=int,
        compute_level="trial",
        aggregates=["sum", "pct"],
        compute_fn=lambda r: (
            1
            if (r.get("status") or "").lower() != "solved"
            and (r.get("failure_category") or "") != "timeout"
            else 0
        ),
        description="1 if trial errored (excluding timeouts), else 0.",
    )
)

register_metric(
    MetricSpec(
        key="solved",
        label="Solved",
        dtype=int,
        compute_level="trial",
        aggregates=["sum", "pct"],
        compute_fn=lambda r: 1 if (r.get("status") or "").lower() == "solved" else 0,
        description="1 if trial solved successfully, else 0.",
    )
)

# ---------------------------------------------------------
# Run-level timing metrics (from progress.log)
# ---------------------------------------------------------


def _run_wall_time(r):
    trials = _trials(r)
    if not trials:
        return None

    starts = [t.get("started_at") for t in trials if isinstance(t.get("started_at"), (int, float))]
    finishes = [
        t.get("finished_at") for t in trials if isinstance(t.get("finished_at"), (int, float))
    ]

    if not starts or not finishes:
        return None

    return max(finishes) - min(starts)


register_metric(
    MetricSpec(
        key="run_wall_time",
        label="Wall\nTime\n(m:s)",
        dtype=float,
        fmt="duration_hms",
        compute_level="run",
        is_invariant=False,
        aggregates=[],
        compute_fn=_run_wall_time,
        description="Total wall-clock time for the run (from first start to last finish).",
    )
)

register_metric(
    MetricSpec(
        key="throughput",
        label="Trials/s",
        dtype=float,
        compute_level="run",
        aggregates=[],
        fmt="float2",
        compute_fn=lambda r: r.get("throughput"),
        description="Number of trials completed per second of wall-clock time.",
    )
)

# ---------------------------------------------------------
# Optional (highly recommended): efficiency metric
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="efficiency",
        label="Eff.",
        dtype=float,
        compute_level="run",
        aggregates=[],
        fmt="float2",
        compute_fn=lambda r: (
            (r.get("throughput") / r.get("trial_jobs"))
            if r.get("throughput") and r.get("trial_jobs")
            else None
        ),
        description="Throughput normalized by number of parallel trial jobs.",
    )
)


def _total_elapsed_seconds(r):
    # _debug_row(r)
    trials = (r.get("_ctx") or {}).get("trial_rows") or []
    run_id = r.get("run_id")

    total = 0.0

    for t in trials:
        if t.get("run_id") != run_id:
            continue

        val = t.get("elapsed_seconds") or (t.get("timing") or {}).get("elapsed_seconds")

        if isinstance(val, (int, float)):
            total += val

    return total if total > 0 else None


def _wall_time_efficiency(r):
    wall = _run_wall_time(r)
    total = _total_elapsed_seconds(r)

    if not wall or not total:
        return None

    return total / wall


register_metric(
    MetricSpec(
        key="wall_time_efficiency",
        label="Wall\nEffic.",
        dtype=float,
        fmt="float2",
        compute_level="run",
        compute_fn=_wall_time_efficiency,
        description="Total compute time divided by elapsed wall time (≈ effective parallelism).",
        value_series_fn=wrap_value_fn(lambda v, _: f"{v:.1f}× parallel"),
    )
)

dummy = 0


def _solver_efficiency_trial(r):
    solve = (r.get("timing") or {}).get("elapsed_seconds")
    wall = r.get("elapsed_seconds")

    if not isinstance(solve, (int, float)):
        return None
    if not isinstance(wall, (int, float)) or wall <= 0:
        return None

    return solve / wall


register_metric(
    MetricSpec(
        key="solver_efficiency",
        label="Solve\nEffic.",
        dtype=float,
        fmt="percent",
        compute_level="trial",
        compute_fn=_solver_efficiency_trial,
        aggregates=["median", "p10", "p90"],
        description="Fraction of trial time spent inside solver.",
    )
)


def _solver_efficiency_run(r):
    trials = _trials(r)

    total_solve = 0.0
    total_wall = 0.0

    for t in trials:
        solve = (t.get("timing") or {}).get("elapsed_seconds")
        wall = t.get("elapsed_seconds")

        if not isinstance(solve, (int, float)):
            continue
        if not isinstance(wall, (int, float)) or wall <= 0:
            continue

        total_solve += solve
        total_wall += wall

    return total_solve / total_wall if total_wall else None


register_metric(
    MetricSpec(
        key="solver_efficiency_run",
        label="Solve %",
        dtype=float,
        fmt="percent",
        compute_level="run",
        compute_fn=_solver_efficiency_run,
        description="Fraction of total runtime spent solving (weighted).",
    )
)

def _compute_overhead_ratio(r):
    try:
        wall = r.get("run_wall_time")
        jobs = r.get("trial_jobs")
        trials = _trial_total(r)

        trial_rows = _trials(r)
        elapsed_vals = [
            t.get("elapsed_seconds")
            for t in trial_rows
            if isinstance(t.get("elapsed_seconds"), (int, float))
        ]

        if not wall or not jobs or not trials or not elapsed_vals:
            return None

        mean_elapsed = sum(elapsed_vals) / len(elapsed_vals)

        ideal = (mean_elapsed * trials) / jobs

        if ideal <= 0:
            return None

        return wall / ideal

    except Exception:
        return None
    
    
register_metric(
    MetricSpec(
        key="overhead_ratio",
        label="Overhead",
        dtype=float,
        fmt="float2",
        compute_level="run",
        compute_fn=lambda r: _compute_overhead_ratio(r),
        description="Ratio of wall time to ideal parallel execution time.",
    )
)