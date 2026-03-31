from ..formatting import format_value
from .metric_registry import register_metric
from .metric_spec import MetricSpec

# =========================================================
# Helpers
# =========================================================


def _bool_value(value: bool, true_msg: str, false_msg: str) -> str:
    return true_msg if value else false_msg


def wrap_value_fn(fn):
    def series_fn(values, raw, rows):
        clean = [v for v in values if v is not None]
        if not clean:
            return "-"
        return fn(clean[0], rows[0] if rows else None)

    return series_fn


# =========================================================
# CORE OUTCOMES
# =========================================================

register_metric(
    MetricSpec(
        key="spending_annual",
        path="financial.spending.year0.today",
        label="Annual Spending",
        fmt="currency",
        aggregates=["median"],
        description="Annual spending in today's dollars at the start of retirement (year 0).",
    )
)

register_metric(
    MetricSpec(
        key="spending_total",
        path="financial.spending.total.today",
        label="Total Spending",
        fmt="currency",
        aggregates=["median"],
        description="Total lifetime spending in today's dollars across the full planning horizon.",
    )
)

register_metric(
    MetricSpec(
        key="bequest",
        path="financial.bequest.total.today",
        label="Bequest",
        fmt="currency",
        aggregates=["median", "mean"],
        description="Remaining estate value at the end of the plan after all spending and taxes.",
    )
)

register_metric(
    MetricSpec(
        key="ending_assets",
        path="risk.outcome.assets.final_today",
        label="Ending Assets",
        fmt="currency",
        aggregates=["median"],
        description="Total assets remaining at the end of the plan in today's dollars.",
    )
)


# =========================================================
# STATUS
# =========================================================

register_metric(
    MetricSpec(
        key="status",
        path="run_status.status",
        label="Status",
        dtype=str,
        description="Outcome of the solver for this trial (solved or failed).",
        value_series_fn=wrap_value_fn(lambda v, _: "Solved" if v == "solved" else "Failed"),
    )
)

register_metric(
    MetricSpec(
        key="success",
        label="Success",
        compute_fn=lambda d: 1 if d.get("status") == "solved" else 0,
        fmt="percent",
        aggregates=["cnt", "pct"],
        description="Indicates whether the plan solved successfully (1) or failed (0).",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Successful outcome", "Unsuccessful outcome")
        ),
    )
)

register_metric(
    MetricSpec(
        key="solver_fail",
        label="Solver\nFail",
        dtype=int,
        aggregates=[("cnt_true", "int"), ("pct", "percent")],
        compute_fn=lambda r: 0 if r.get("status") == "solved" else 1,
        description="Indicator that the solver failed to produce a valid plan.",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Solver failure occurred", "No solver failure")
        ),
    )
)

register_metric(
    MetricSpec(
        key="elapsed",
        path="timing.elapsed_seconds",
        label="Elapsed",
        fmt="float2",
        aggregates=["mean"],
        description="Time taken to solve the plan in seconds.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{format_value(v, 'float2')} seconds"),
    )
)

# =========================================================
# INPUT CONTEXT
# =========================================================

register_metric(
    MetricSpec(
        key="case_name",
        label="Case",
        dtype=str,
        is_invariant=True,
        description="Name of the planning case or scenario.",
    )
)

register_metric(
    MetricSpec(
        key="experiment",
        label="Exp",
        aggregates=["cnt"],
        description="Experiment identifier grouping multiple runs.",
    )
)

register_metric(
    MetricSpec(
        key="run",
        label="Run",
        aggregates=["cnt"],
        description="Run identifier within an experiment.",
    )
)

register_metric(
    MetricSpec(
        key="trial",
        label="Trial",
        aggregates=["cnt"],
        description="Number of simulation trials in the run.",
    )
)

register_metric(
    MetricSpec(
        key="rates_method",
        path="_inputs.rates_selection.method",
        label="Rates Method",
        dtype=str,
        description="Method used to generate return and inflation scenarios.",
    )
)

register_metric(
    MetricSpec(
        key="objective",
        path="_inputs.optimization_parameters.objective",
        label="Objective",
        dtype=str,
        description="Optimization objective used in the plan (e.g., maximize spending or bequest).",
    )
)

# Overrides

# =========================================================
# OVERRIDES (CONTEXT-BASED — CORRECT IMPLEMENTATION)
# =========================================================


def _format_override_dict(d: dict | None) -> str:
    """
    Format override dict into readable multi-line string.
    """
    if not d:
        return "-"

    return "\n".join(f"{k} = {v}" for k, v in sorted(d.items()))


def _override_value_series_fn(values, raw, rows):
    """
    Handles invariant override dictionaries for display and explain.

    values → aggregated values (ignored for dicts)
    raw    → per-row values (what we want)
    rows   → full rows (not needed here)
    """
    clean = [v for v in raw if isinstance(v, dict) and v]

    if not clean:
        return "-"

    # If all identical → display clean dict
    first = clean[0]
    if all(v == first for v in clean):
        return _format_override_dict(first)

    # Fallback (should not happen with invariant=True, but safe)
    return "\n".join(_format_override_dict(v) for v in clean[:3])


register_metric(
    MetricSpec(
        key="run_specific_overrides",
        label="Run-specific overrides",
        dtype=dict,
        fmt="overrides",
        is_invariant=True,
        compute_fn=lambda d: d.get("run_specific_overrides"),
        description=(
            "Overrides that vary across runs (e.g., parameter sweeps such as "
            "solver_options.spendingSlack)."
        ),
        value_series_fn=_override_value_series_fn,
    )
)


register_metric(
    MetricSpec(
        key="common_overrides",
        label="Common overrides",
        dtype=dict,
        fmt="overrides",
        is_invariant=True,
        compute_fn=lambda d: d.get("common_overrides"),
        description=(
            "Overrides shared across all runs in the experiment "
            "(e.g., rates_selection.method, date ranges)."
        ),
        value_series_fn=_override_value_series_fn,
    )
)

# =========================================================
# RISK
# =========================================================

register_metric(
    MetricSpec(
        key="min_cushion",
        path="risk.outcome.cushion.min_cushion_ratio",
        label="Min Cushion",
        fmt="float2",
        aggregates=["mean"],
        description="Minimum ratio of assets to spending observed over the lifetime of the plan.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"{format_value(v, 'float2')}× spending buffer at minimum point"
        ),
    )
)

register_metric(
    MetricSpec(
        key="worst_drawdown",
        path="risk.outcome.drawdown.worst_drawdown_factor",
        label="Worst Drawdown",
        fmt="percent2",
        aggregates=["mean"],
        description="Largest peak-to-trough decline in portfolio value during the plan.",
    )
)

register_metric(
    MetricSpec(
        key="terminal_ratio",
        path="risk.outcome.terminal.spending_to_assets_ratio",
        label="Terminal S/A",
        fmt="percent2",
        aggregates=["mean"],
        description="Final ratio of spending to remaining assets at the end of the plan.",
    )
)

register_metric(
    MetricSpec(
        key="terminal_assets_to_spending",
        label="Terminal A/S",
        fmt="float2",
        aggregates=["mean"],
        compute_fn=lambda r: (
            1 / r.get("terminal_ratio") if r.get("terminal_ratio") not in (None, 0) else None
        ),
        description="Final assets divided by final spending (inverse of spending-to-assets ratio).",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Assets cover {format_value(v, 'float2')}× final spending"
        ),
    )
)

register_metric(
    MetricSpec(
        key="risk",
        path="risk.outcome.classification.risk_level",
        label="Risk",
        dtype=str,
        description="Overall risk classification (low, moderate, high, failure).",
    )
)


# =========================================================
# SPENDING STRESS (PRECOMPUTED)
# =========================================================

register_metric(
    MetricSpec(
        key="spending_ratio_min",
        path="financial.spending_summary.min_ratio",
        label="Worst\nSpending",
        fmt="percent2",
        aggregates=["mean", "p10"],
        description="Lowest spending level achieved relative to baseline spending.",
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "Plan collapses (0% spending)"
                if v == 0
                else f"Worst-case spending falls to {format_value(v, 'percent2')} of target"
            )
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_mean",
        path="financial.spending_summary.mean_ratio",
        label="Avg\nSpending",
        fmt="percent2",
        aggregates=["mean"],
        description="Average spending level relative to baseline across all years.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Average lifestyle maintained at {format_value(v, 'percent2')}"
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_median",
        path="financial.spending_summary.median_ratio",
        label="Median\nSpending",
        fmt="percent2",
        aggregates=["mean"],
        description="Median (typical) spending relative to baseline across years.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Typical spending is {format_value(v, 'percent2')} of baseline"
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_p10",
        path="financial.spending_summary.p10_ratio",
        label="P10\nSpending",
        fmt="percent2",
        aggregates=["mean"],
        description="10th percentile spending level, representing downside risk.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Downside (P10) spending is {format_value(v, 'percent2')} of target"
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_shortfall",
        path="financial.spending_summary.shortfall",
        label="Shortfall",
        fmt="percent2",
        aggregates=["mean", "p90"],
        description="Maximum reduction required from baseline spending.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Requires {format_value(v, 'percent2')} spending reduction"
        ),
    )
)

register_metric(
    MetricSpec(
        key="required_slack",
        path="financial.spending_summary.required_slack",
        label="Required\nSlack",
        fmt="percent2",
        aggregates=["mean", "p90"],
        description="Minimum spending flexibility required to sustain the plan.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Requires {format_value(v, 'percent2')} flexibility"
        ),
    )
)

register_metric(
    MetricSpec(
        key="years_under_target",
        path="financial.spending_summary.years_under_target",
        label="Years\n< Target",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Number of years in which spending falls below baseline target.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years below target spending"),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_std",
        path="financial.spending_summary.std_ratio",
        label="Spending\nVolatility",
        fmt="float2",
        aggregates=["mean"],
        description="Volatility of spending relative to baseline across the plan horizon.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Spending volatility of {format_value(v, 'float2')}"
        ),
    )
)

# =========================================================
# MINIMUM SPENDING (FLOOR SAFETY)
# =========================================================

register_metric(
    MetricSpec(
        key="spending_ratio_to_minimum_min",
        path="financial.spending_summary.min_ratio_to_minimum",
        label="Worst\nvs Floor",
        fmt="percent2",
        aggregates=["mean", "p10"],
        description="Lowest spending relative to minimum required spending.",
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "Falls below minimum spending"
                if v < 1
                else f"Always above floor (min {format_value(v, 'percent2')})"
            )
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_minimum_mean",
        path="financial.spending_summary.mean_ratio_to_minimum",
        label="Avg\nvs Floor",
        fmt="percent2",
        aggregates=["mean"],
        description="Average spending relative to minimum spending.",
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_minimum_median",
        path="financial.spending_summary.median_ratio_to_minimum",
        label="Median\nvs Floor",
        fmt="percent2",
        aggregates=["mean"],
        description="Median spending relative to minimum spending.",
    )
)

register_metric(
    MetricSpec(
        key="years_below_minimum",
        path="financial.spending_summary.years_below_minimum",
        label="Years\n< Floor",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Number of years spending falls below minimum spending level.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years below minimum spending"),
    )
)

register_metric(
    MetricSpec(
        key="floor_breach",
        path="financial.spending_summary.floor_breach",
        label="Floor\nBreach",
        dtype=int,
        aggregates=[("cnt_true", "int"), ("pct", "percent")],
        description="Indicates whether spending ever falls below minimum level.",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Floor breached", "Floor never breached")
        ),
    )
)

# =========================================================
# ACCEPTABLE SPENDING (BEHAVIORAL TOLERANCE)
# =========================================================

register_metric(
    MetricSpec(
        key="spending_ratio_to_acceptable_min",
        path="financial.spending_summary.min_ratio_to_acceptable",
        label="Worst\nvs Acceptable",
        fmt="percent2",
        aggregates=["mean", "p10"],
        description="Lowest spending relative to acceptable lifestyle level.",
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "Below acceptable lifestyle"
                if v < 1
                else f"Maintains acceptable level (min {format_value(v, 'percent2')})"
            )
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_acceptable_mean",
        path="financial.spending_summary.mean_ratio_to_acceptable",
        label="Avg\nvs Acceptable",
        fmt="percent2",
        aggregates=["mean"],
        description="Average spending relative to acceptable level.",
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_acceptable_median",
        path="financial.spending_summary.median_ratio_to_acceptable",
        label="Median\nvs Acceptable",
        fmt="percent2",
        aggregates=["mean"],
        description="Median spending relative to acceptable level.",
    )
)

register_metric(
    MetricSpec(
        key="years_below_acceptable",
        path="financial.spending_summary.years_below_acceptable",
        label="Years\n< Acceptable",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Number of years spending falls below acceptable level.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years below acceptable spending"),
    )
)

register_metric(
    MetricSpec(
        key="consecutive_years_below_acceptable",
        path="financial.spending_summary.consecutive_years_below_acceptable",
        label="Consec\n< Acceptable",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Maximum consecutive years below acceptable spending.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} consecutive years below acceptable"),
    )
)

register_metric(
    MetricSpec(
        key="spending_stress_flag",
        path="financial.spending_summary.spending_stress_flag",
        label="Stress",
        dtype=int,
        aggregates=[("cnt_true", "int"), ("pct", "percent")],
        description="Indicates whether spending falls below acceptable level at any point.",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Stress triggered", "No stress")
        ),
    )
)

# =========================================================
# DERIVED RELATIONSHIP
# =========================================================

register_metric(
    MetricSpec(
        key="years_between_min_and_target",
        path="financial.spending_summary.years_between_min_and_target",
        label="Years\nAdaptive",
        fmt="int",
        aggregates=["mean"],
        description="Years where spending is below target but above minimum (adaptive zone).",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years in adaptive zone"),
    )
)
