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
        label="Annual\nSpending",
        fmt="currency_short",
        aggregates=["median"],
        description="Annual spending in today's dollars at the start of retirement (year 0).",
    )
)

register_metric(
    MetricSpec(
        key="spending_total",
        path="financial.spending.total.today",
        label="Total\nSpending",
        fmt="currency_short",
        aggregates=["median"],
        description="Total lifetime spending in today's dollars across the full planning horizon.",
    )
)

register_metric(
    MetricSpec(
        key="taxes_total",
        path="financial.taxes.total.today",
        label="Total\nTaxes",
        fmt="currency_short",
        aggregates=["median"],
        description="Total lifetime taxes in today's dollars across the full planning horizon.",
    )
)


register_metric(
    MetricSpec(
        key="bequest",
        path="financial.bequest.total.today",
        label="Bequest",
        fmt="currency_short",
        aggregates=["median", "mean"],
        description="Remaining estate value at the end of the plan after all spending and taxes.",
    )
)

register_metric(
    MetricSpec(
        key="ending_assets",
        path="risk.outcome.assets.final_today",
        label="Ending Assets",
        fmt="currency_short",
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
        label="Case name",
        dtype=str,
        align="left",
        is_invariant=True,
        description="Name of the planning case or scenario.",
    )
)

register_metric(
    MetricSpec(
        key="case",
        label="Case",
        aggregates=["cnt"],
        description="Case identifier for grouping experiments..",
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


def _format_run_id(r):
    case = r.get("case")
    exp = r.get("experiment")
    run = r.get("run")

    if case is None or exp is None or run is None:
        return None

    return f"{case}/{exp}/{run}"


register_metric(
    MetricSpec(
        key="run_id_compact",
        label="Case/\n Exp/\nRun",
        dtype=str,
        align="center",
        compute_fn=lambda r: _format_run_id(r),
        description="Compact identifier: case/experiment/run",
    )
)

register_metric(
    MetricSpec(
        key="trial",
        label="Trls",
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
        key="rates_values",
        path="_inputs.rates_selection.values",
        label="Rates values",
        dtype=str,
        description="Values associated with selected method.",
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


def _compute_goal_from_inputs(r):
    obj = r.get("objective")

    inputs = r.get("_inputs", {})
    solver = inputs.get("solver_options", {})

    # ----------------------------------------
    # 1. Get raw value
    # ----------------------------------------
    if obj == "maxSpending":
        raw = solver.get("bequest")

    elif obj == "maxBequest":
        raw = solver.get("netSpending")

    else:
        return None

    if raw is None:
        return None

    # ----------------------------------------
    # 2. Normalize units → dollars
    # ----------------------------------------
    units = solver.get("units", "k")  # default dollars

    try:
        v = float(raw)
    except Exception:
        return None

    if units == "k":
        return v * 1_000
    elif units == "M":
        return v * 1_000_000
    else:  # "1"
        return v


def _format_goal(value, row):
    if value is None:
        return "-"

    obj = row.get("objective")

    def short_currency(v):
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"${int(v/1000)}K"
        return f"${int(v)}"

    val = short_currency(value)

    if obj == "maxSpending":
        return f"MaxSpnd·Beq={val}"

    if obj == "maxBequest":
        return f"MaxBeq·Spnd={val}"

    return val


register_metric(
    MetricSpec(
        key="goal",
        label="Goal",
        align="left",
        compute_fn=_compute_goal_from_inputs,
        is_invariant=True,  # 🔥 important: comes from inputs, not trials
        description="User-defined optimization goal (constraint target).",
        display_row_fn=lambda v, row, ctx: _format_goal(v, row),
        value_series_fn=lambda values, rows, *_: (
            _format_goal(values[0], rows[0]) if values and rows else "-"
        ),
    )
)


def _format_number(v):
    try:
        f = float(v)
    except Exception:
        return str(v)

    # remove trailing .0 if integer
    if f.is_integer():
        return str(int(f))

    return str(f)


def _format_rates(r):
    inputs = r.get("_inputs", {})
    rates = inputs.get("rates_selection", {})

    method = rates.get("method")

    # ----------------------------------------
    # Historical bootstrap (SoR)
    # ----------------------------------------
    if method == "bootstrap_sor":
        start = rates.get("from")
        end = rates.get("to")

        if start and end:
            return f"Hist ({start}–{end})"
        return "Hist"

    # ----------------------------------------
    # User-defined rates
    # ----------------------------------------
    if method == "user":
        vals = rates.get("values") or []
        if vals:
            vals_str = "/".join(_format_number(v) for v in vals)
            return f"User ({vals_str})"
        return "User"

    # ----------------------------------------
    # Fallback
    # ----------------------------------------
    return method or "-"


register_metric(
    MetricSpec(
        key="rates",
        label="Rates",
        align="left",
        compute_fn=_format_rates,
        is_invariant=True,
        description="Compact description of return scenario generation method.",
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


# SPENDING PROFILE

register_metric(
    MetricSpec(
        key="spending_now",
        path="financial.spending_profile.year0",
        label="Spending\n(Now)",
        fmt="currency_short",
        aggregates=["median"],
        description="Spending in today's dollars at the start of retirement.",
    )
)

register_metric(
    MetricSpec(
        key="spending_early",
        path="financial.spending_profile.early_avg",
        label="Spending\n(Early)",
        fmt="currency_short",
        aggregates=["median"],
        description="Average spending over the early retirement period (first ~5 years).",
    )
)

register_metric(
    MetricSpec(
        key="spending_late",
        path="financial.spending_profile.late_avg",
        label="Spending\n(Late)",
        fmt="currency_short",
        aggregates=["median"],
        description="Average spending in later years (typically survivor phase).",
    )
)

register_metric(
    MetricSpec(
        key="spending_survivor_ratio",
        path="financial.spending_profile.survivor_ratio",
        label="Survivor\nRatio",
        fmt="percent",
        aggregates=["mean"],
        description="Ratio of late-life spending to early-life spending.",
    )
)

register_metric(
    MetricSpec(
        key="spending_final",
        path="financial.spending_profile.yearN",
        label="Final\nSpending",
        fmt="currency_short",
        aggregates=["median"],
        description="Spending in the final year of the plan.",
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
        key="outcome_risk",
        path="risk.outcome.classification.risk_level",
        label="Outcome\nRisk",
        dtype=str,
        description="Risk classification based on plan outcomes only (ignores scenario severity).",
    )
)

register_metric(
    MetricSpec(
        key="overall_risk",
        path="risk.summary.overall_risk",
        label="Overall\nRisk",
        dtype=str,
        description=(
            "Composite risk classification based on asset drawdown, depletion pressure, "
            "and spending intensity.\n"
            "In single-trial runs, this reflects structural fragility—not probability of failure."
        ),
    )
)

register_metric(
    MetricSpec(
        key="scenario_severity",
        path="risk.summary.scenario_severity",
        label="Scenario\nSeverity",
        fmt="percent2",
        aggregates=["mean"],
        description="Normalized severity of the return environment.",
    )
)

register_metric(
    MetricSpec(
        key="depleted",
        path="risk.summary.depleted",
        label="Depleted",
        dtype=int,
        fmt="count_ratio",
        aggregates=[("ratio", "count_ratio")],
        description="Indicates whether assets are depleted during the plan.",
    )
)

register_metric(
    MetricSpec(
        key="risk_flag_count",
        path="risk.summary.flag_count",
        label="Risk\nFlags",
        fmt="int",
        aggregates=["mean"],
        description="Number of risk signals triggered in scenario and outcome.",
    )
)

FLAG_EXPLANATIONS = {
    "ending_asset_erosion": (
        "Financial assets decline significantly late in life. This may reflect "
        "planned use or conversion of assets (e.g., home sale), not necessarily risk."
    ),
    "high_spending_pressure": (
        "Spending uses a large portion of financial assets. This may be acceptable "
        "if supported by other assets or planned drawdown."
    ),
    "severe_asset_drawdown": (
        "Financial assets experience large declines. In some plans, this reflects "
        "intentional drawdown or asset conversion rather than adverse outcomes."
    ),
}

register_metric(
    MetricSpec(
        key="risk_flags",
        path="risk.summary.flags",
        label="Risk\nSignals",
        dtype=str,
        aggregates=[],
        description=(
            "Indicators of plan fragility (asset drawdown, depletion pressure, etc.). "
            "These do not imply spending failure."
        ),
        value_series_fn=lambda values, *_: "\n\n".join(
            f"{f.replace('_', ' ').capitalize()}:\n{FLAG_EXPLANATIONS.get(f, '')}"
            for f in sorted(set(f for v in values if isinstance(v, list) for f in v))
        ),
        display_row_fn=lambda v, row, ctx: (
            "\n".join(f.replace("_", " ").capitalize() for f in v)
            if isinstance(v, list) and v
            else "-"
        ),
    )
)

register_metric(
    MetricSpec(
        key="risk_reconciliation",
        label="Risk\nInterpretation",
        dtype=str,
        aggregates=[],
        display_row_fn=lambda v, row, ctx: (
            "see explain=values"
            if isinstance(row, dict)
            and row.get("overall_risk") == "high"
            and row.get("years_below_acceptable", 0) == 0
            else "-"
        ),
        value_series_fn=lambda values, rows, *_: (
            "Spending remains strong across all years. Asset-based signals reflect "
            "drawdown of financial assets, which may include planned liquidation of "
            "non-financial assets (e.g., home sale), not necessarily risk to lifestyle."
            if rows
            and any(
                isinstance(r, dict)
                and r.get("overall_risk") == "high"
                and r.get("years_below_acceptable", 0) == 0
                for r in rows
            )
            else ""
        ),
    )
)


# =========================================================
# SPENDING STRESS (PRECOMPUTED)
# =========================================================

register_metric(
    MetricSpec(
        key="minimum_spending",
        path="financial.risk_analysis.minimum_spending",
        label="Minimum\nspending",
        fmt="currency",
        dtype=float,
        is_invariant=True,
        description="Minimum lifestyle spending level (safety, user-input).",
    )
)

register_metric(
    MetricSpec(
        key="acceptable_spending",
        path="financial.risk_analysis.acceptable_spending",
        label="Acceptable\nspending",
        fmt="currency",
        dtype=float,
        is_invariant=True,
        description="Base acceptable spending level (scaled by household profile over time).",
    )
)


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
        label="Worst Year/\nMinimum",
        fmt="percent2",
        aggregates=["mean", "p10"],
        description="Lowest spending relative to minimum spending (safety).",
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "Falls below minimum spending"
                if v < 1
                else f"Always above minimum spending (min {format_value(v, 'percent2')})"
            )
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_minimum_mean",
        path="financial.spending_summary.mean_ratio_to_minimum",
        label="Avg Year/\nMinimum",
        fmt="percent2",
        aggregates=["mean"],
        description="Average spending relative to minimum spending.",
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_minimum_median",
        path="financial.spending_summary.median_ratio_to_minimum",
        label="Median Year/\nMinimum",
        fmt="percent2",
        aggregates=["mean"],
        description="Median spending relative to minimum spending.",
    )
)

register_metric(
    MetricSpec(
        key="years_below_minimum",
        path="financial.spending_summary.years_below_minimum",
        label="Years\n< Minimum",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Number of years spending falls below minimum spending level.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years below minimum spending"),
    )
)

register_metric(
    MetricSpec(
        key="consecutive_years_below_minimum",
        path="financial.spending_summary.consecutive_years_below_minimum",
        label="Consec <\nMinimum",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Maximum consecutive years spending falls below minimum spending level.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"{int(v)} consecutive years below minimum spending"
        ),
    )
)

register_metric(
    MetricSpec(
        key="floor_breach",
        path="financial.spending_summary.floor_breach",
        label="Minimum\nBreach",
        dtype=int,
        fmt="count_ratio",
        aggregates=[("ratio", "count_ratio")],
        description="Number of trials where spending falls below minimum spending at any year of trial.",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Minimum breached", "Minimum never breached")
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
        label="Worst Year/\nAcceptable",
        fmt="percent2",
        aggregates=["mean", "p10"],
        description="Lowest spending relative to acceptable lifestyle (adjusted for household size via xi_n).",
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
        label="Avg Year/\nAcceptable",
        fmt="percent2",
        aggregates=["mean"],
        description="Average spending relative to acceptable level.",
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_acceptable_median",
        path="financial.spending_summary.median_ratio_to_acceptable",
        label="Median Year/\nAcceptable",
        fmt="percent2",
        aggregates=["mean"],
        description="Median spending relative to acceptable level.",
    )
)

register_metric(
    MetricSpec(
        key="years_below_acceptable",
        path="financial.spending_summary.years_below_acceptable",
        label="Years <\nAcceptable",
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
        label="Consec <\nAcceptable",
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
        label="Acceptable\nBreach",
        dtype=int,
        fmt="count_ratio",
        aggregates=[("ratio", "count_ratio")],
        description="Number of trials where spending falls below acceptable level at any year in trial.",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Stress triggered", "No stress")
        ),
    )
)

# =========================================================
# SPENDING - worst spending avlue
# =========================================================


def _compute_spending_worst(r):
    series = (
        r.get("financial", {})
        .get("timeseries", {})
        .get("spending", {})
        .get("actual", {})
        .get("today_by_year", [])
    )

    if not series:
        return None

    clean = [v for v in series if v is not None]
    if not clean:
        return None

    return min(clean)


register_metric(
    MetricSpec(
        key="spending_worst",
        label="Worst\nSpending",
        fmt="currency",  # ✅ now works
        aggregates=["mean", "median", "p90"],  # safe even for 1 trial
        compute_fn=_compute_spending_worst,
        description=(
            "Lowest annual spending observed across the plan horizon, "
            "measured in today's dollars."
        ),
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Worst spending falls to {format_value(v, 'currency')}"
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

# =========================================================
# RUN PROFILING / DASHBOARD FLAGS
# =========================================================


def _has_override(r, key_fragment: str) -> bool:
    overrides = r.get("run_specific_overrides") or {}
    return any(key_fragment in k for k in overrides)


def _run_profile(r):
    flags = []

    overrides = r.get("run_specific_overrides") or {}

    if "social_security_ages" in overrides:
        flags.append("SS")

    if "solver_options.spendingSlack" in overrides:
        flags.append("Slack")

    if r.get("rates_method") == "bootstrap_sor":
        flags.append("SoR")

    if any("roth" in k for k in overrides):
        flags.append("Roth")

    return ", ".join(flags) if flags else "Base"


# ---------------------------------------------------------
# PROFILE LABEL (compact descriptor)
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="run_profile",
        label="Profile",
        align="left",
        dtype=str,
        compute_fn=_run_profile,
        is_invariant=True,
        description="High-level classification of the experiment intent",
    )
)


# ---------------------------------------------------------
# INDIVIDUAL FLAGS (yes / -)
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="is_ss_experiment",
        label="SS",
        dtype=int,
        compute_fn=lambda r: 1 if _has_override(r, "social_security_ages") else 0,
        value_series_fn=wrap_value_fn(lambda v, _: "yes" if v == 1 else "-"),
        description="Run varies Social Security claiming strategy",
    )
)

register_metric(
    MetricSpec(
        key="is_spending_slack",
        label="Slack",
        dtype=int,
        compute_fn=lambda r: 1 if _has_override(r, "spendingSlack") else 0,
        value_series_fn=wrap_value_fn(lambda v, _: "yes" if v == 1 else "-"),
        description="Run explores spending flexibility",
    )
)

register_metric(
    MetricSpec(
        key="is_sor_experiment",
        label="SoR",
        dtype=int,
        compute_fn=lambda r: 1 if r.get("rates_method") == "bootstrap_sor" else 0,
        value_series_fn=wrap_value_fn(lambda v, _: "yes" if v == 1 else "-"),
        description="Run explores sequence-of-returns risk",
    )
)

register_metric(
    MetricSpec(
        key="is_roth_strategy",
        label="Roth",
        dtype=int,
        compute_fn=lambda r: 1 if _has_override(r, "roth") else 0,
        value_series_fn=wrap_value_fn(lambda v, _: "yes" if v == 1 else "-"),
        description="Run explores Roth conversion or tax strategy",
    )
)

register_metric(
    MetricSpec(
        key="has_overrides",
        label="Varies",
        dtype=int,
        compute_fn=lambda r: 1 if (r.get("run_specific_overrides") or {}) else 0,
        value_series_fn=wrap_value_fn(lambda v, _: "yes" if v == 1 else "-"),
        description="Run varies one or more key inputs",
    )
)


# ---------------------------------------------------------
# ATTENTION / QUALITY FLAGS
# ---------------------------------------------------------


def _needs_attention(r):
    """
    Conservative flag:
    highlight anything that deserves a closer look.
    """
    if r.get("solver_fail"):
        return 1

    if r.get("floor_breach"):
        return 1

    ratio = r.get("spending_ratio_min")
    if ratio is not None and ratio < 0.85:
        return 1

    return 0


def _bad_run(r):
    """
    Strong failure flag:
    clearly unacceptable plans.
    """
    if r.get("solver_fail"):
        return 1

    if r.get("floor_breach"):
        return 1

    ratio = r.get("spending_ratio_min")
    if ratio is not None and ratio < 0.70:
        return 1

    return 0


register_metric(
    MetricSpec(
        key="needs_attention",
        label="Review",
        dtype=int,
        compute_fn=_needs_attention,
        aggregates=[("cnt_true", "int"), ("pct", "percent")],
        description="Run shows warning signs and should be reviewed",
        value_series_fn=wrap_value_fn(lambda v, _: "⚠️ yes" if v == 1 else "-"),
    )
)

register_metric(
    MetricSpec(
        key="bad_run_flag",
        label="Bad",
        dtype=int,
        compute_fn=_bad_run,
        aggregates=[("cnt_true", "int"), ("pct", "percent")],
        description="Run is clearly unacceptable (failure or severe spending collapse)",
        value_series_fn=wrap_value_fn(lambda v, _: "❌ yes" if v == 1 else "-"),
    )
)


def _run_status(r):
    if r.get("solver_fail"):
        return "Fail"

    if r.get("floor_breach"):
        return "Below minimum"

    ratio = r.get("spending_ratio_min")

    if ratio is not None:
        if ratio < 0.70:
            return "Collapse"
        if ratio < 0.85:
            return "Stress"

    return "✓ OK"


register_metric(
    MetricSpec(
        key="run_status_summary",
        label="Status",
        dtype=str,
        compute_fn=_run_status,
        description="Overall run quality classification (fail, stress, ok)",
    )
)
