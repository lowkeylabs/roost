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
        is_invariant=True,  # 🔥 THIS is the key change
        compute_fn=lambda r: r.get("worker_timeout"),
        description="Configured worker timeout (seconds).",
        value_series_fn=wrap_value_fn(lambda v, *_: f"{v}s" if isinstance(v, int) else (v or "-")),
        display_row_fn=lambda v, *_: (
            f"{v}s" if isinstance(v, int) else (v if isinstance(v, str) else "-")
        ),
    )
)

# ---------------------------------------------------------
# ELAPSED TIME (SECONDS)
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="elapsed_seconds",
        path="timing.elapsed_seconds",
        label="Time (s)",
        fmt="float2",
        dtype=float,
        compute_level="trial",
        aggregates=["median", "p10", "p90", "p99"],
        description="Elapsed solve time per trial (seconds). Aggregated across trials.",
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
