from ..formatting import format_value
from .metric_registry import register_metric
from .metric_spec import MetricSpec

# =========================================================
# Helpers
# =========================================================


def _bool_value(value: bool, true_msg: str, false_msg: str) -> str:
    return true_msg if value else false_msg


def _range_value(value, low, mid, low_msg, mid_msg, high_msg):
    if value is None:
        return ""
    if value < low:
        return low_msg
    if value < mid:
        return mid_msg
    return high_msg


def _get_unique_metric(rows, key):
    vals = {r.get(key) for r in rows if r.get(key) is not None}
    return next(iter(vals)) if len(vals) == 1 else None


def wrap_value_fn(fn):
    def series_fn(values, raw, rows):
        clean = [v for v in values if v is not None]
        if not clean:
            return "-"
        return fn(clean[0], rows[0] if rows else None)

    return series_fn


# =========================================================
# USER INPUTS
# =========================================================

register_metric(
    MetricSpec(
        key="minimum_spending",
        label="Min Spending Req",
        path="_inputs.risk_analysis.minimum_spending",
        fmt="currency",
        description="Minimum spending before it gets uncomfortable",
    )
)

# =========================================================
# RISK ANALYSIS INPUTS
# =========================================================

register_metric(
    MetricSpec(
        key="soft_fail_consecutive_years_threshold",
        label="Soft Fail\nConsec Years",
        path="_inputs.risk_analysis.soft_fail_consecutive_years_threshhold",
        fmt="int",
        description="Number of consecutive years below minimum spending required to trigger a soft failure",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"{v} consecutive years below minimum spending triggers soft failure"
        ),
    )
)

register_metric(
    MetricSpec(
        key="soft_fail_total_years_threshold",
        label="Soft Fail\nTotal Years",
        path="_inputs.risk_analysis.soft_fail_total_years_threshhold",
        fmt="int",
        description="Total number of years below minimum spending (not necessarily consecutive) required to trigger a soft failure",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"{v} total years below minimum spending triggers soft failure"
        ),
    )
)

register_metric(
    MetricSpec(
        key="soft_fail_min_spending_ratio",
        label="Soft Fail\nMin Ratio",
        path="_inputs.risk_analysis.soft_fail_min_spending_ratio",
        fmt="percent",
        description="Minimum acceptable spending as a fraction of required spending; falling below this triggers a soft failure due to severity",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Spending below {int(v*100)}% of minimum is considered severe shortfall"
        ),
    )
)


register_metric(
    MetricSpec(
        key="net_spending",
        label="Target Spending",
        path="_inputs.financial.net_spending",
        fmt="currency",
    )
)


# =========================================================
# CONTEXT METRICS
# =========================================================

register_metric(
    MetricSpec(
        key="case_name",
        label="Case name",
        dtype=str,
        align="left",
        is_invariant=True,
        description="Name of the household or planning scenario",
        value_series_fn=wrap_value_fn(lambda v, _: f"Result corresponds to case '{v}'"),
    )
)

register_metric(
    MetricSpec(
        key="experiment",
        label="Exp",
        aggregates=["cnt"],
        description="Experiment identifier grouping multiple runs",
        value_series_fn=wrap_value_fn(lambda v, _: f"Part of experiment {v}"),
    )
)

register_metric(
    MetricSpec(
        key="run",
        label="Run",
        aggregates=["cnt"],
        description="Run identifier within an experiment",
        value_series_fn=wrap_value_fn(lambda v, _: f"Run {v} within the experiment"),
    )
)

register_metric(
    MetricSpec(
        key="trial",
        label="Trial",
        dtype=int,
        aggregates=["cnt"],
        description="Trial index within a run",
        value_series_fn=wrap_value_fn(lambda v, _: f"Simulation trial {v}"),
    )
)

register_metric(
    MetricSpec(
        key="master_seed",
        label="Seed",
        compute_fn=lambda d: d.get("master_seed"),
        dtype=int,
        is_invariant=True,
        description="Random seed controlling simulation reproducibility",
        value_series_fn=wrap_value_fn(lambda v, _: f"Deterministic scenario defined by seed {v}"),
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
        align="left",
        description="Outcome status of the optimization run",
        value_series_fn=wrap_value_fn(
            lambda v, _: "Optimization completed successfully"
            if v == "solved"
            else "Optimization did not converge"
        ),
    )
)

register_metric(
    MetricSpec(
        key="elapsed",
        path="timing.elapsed_seconds",
        label="Time (s)",
        fmt="float2",
        aggregates=["mean", "p90"],
        description="Time required to solve the optimization",
        value_series_fn=wrap_value_fn(
            lambda v, _: _range_value(v, 1, 5, "Fast solve", "Moderate solve time", "Slow solve")
        ),
    )
)

register_metric(
    MetricSpec(
        key="success",
        label="Success",
        compute_fn=lambda d: 1 if d.get("status") == "solved" else 0,
        dtype=int,
        fmt="percent",
        aggregates=["cnt", "pct"],
        description="Indicator of successful optimization",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Successful outcome", "Unsuccessful outcome")
        ),
    )
)

register_metric(
    MetricSpec(
        key="fail",
        label="Fail",
        compute_fn=lambda d: 0 if d.get("status") == "solved" else 1,
        dtype=int,
        fmt="percent",
        aggregates=["cnt", "pct"],
        description="Indicator of failed optimization",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Failure occurred", "No failure")
        ),
    )
)

register_metric(
    MetricSpec(
        key="failure_reason",
        path="run_status.failure_category",
        label="Failure Reason",
        dtype=str,
        description="Category of failure when optimization does not solve",
        value_series_fn=wrap_value_fn(lambda v, _: f"Failure categorized as '{v}'" if v else ""),
    )
)

register_metric(
    MetricSpec(
        key="is_failed",
        label="Failed?",
        dtype=bool,
        compute_fn=lambda d: d.get("status") == "failed",
        description="Boolean indicator of failure",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v, "Run failed", "Run did not fail")
        ),
    )
)

register_metric(
    MetricSpec(
        key="is_solved",
        label="Solved?",
        dtype=bool,
        compute_fn=lambda d: d.get("status") == "solved",
        description="Boolean indicator of success",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v, "Run solved", "Run did not solve")
        ),
    )
)

# =========================================================
# FINANCIAL
# =========================================================

register_metric(
    MetricSpec(
        key="bequest",
        path="financial.bequest.total.today",
        label="Bequest",
        fmt="currency",
        aggregates=["mean", "median", "p10", "p90"],
        description="Total wealth remaining at the end of the plan",
        value_series_fn=wrap_value_fn(
            lambda v, _: _range_value(
                v,
                100_000,
                1_000_000,
                "Minimal remaining wealth",
                "Moderate remaining wealth",
                "Substantial remaining wealth",
            )
        ),
    )
)

# =========================================================
# SPENDING SERIES (unchanged)
# =========================================================


def make_spending_series_fn(
    *,
    objective_key="optimization_parameters.objective",
    objective_value="maxBequest",
    invariant_msg="Value is fixed by optimization objective",
    violation_msg="Expected invariant value but found differences",
    fmt=None,
    round_to=None,
):
    def normalize_for_comparison(v, round_to=None):
        if isinstance(v, float):
            if round_to is not None:
                return round(v, round_to)
            return round(v, 6)
        return v

    def fn(values, raw, rows):
        clean = [v for v in raw if v is not None] or [v for v in values if v is not None]
        if not clean:
            return "-"

        norm = [normalize_for_comparison(v, round_to) for v in clean]
        unique = list(dict.fromkeys(norm))

        try:
            objective = _get_unique_metric(rows, objective_key)
        except Exception:
            objective = None

        if objective == objective_value:
            return invariant_msg if len(unique) == 1 else violation_msg

        if len(unique) == 1:
            return format_value(clean[0], fmt)

        return f"{len(unique)} distinct values"

    return fn


register_metric(
    MetricSpec(
        key="spending_total",
        path="financial.spending.total.today",
        label="Total\nSpending",
        fmt="currency",
        aggregates=["mean", "median", "p10", "p90"],
        description="Total lifetime spending",
        value_series_fn=make_spending_series_fn(
            objective_key="objective",
            objective_value="maxBequest",
            invariant_msg="Total spending is fixed to annual spending (objective=maxBequest)",
            violation_msg="Total spending SHOULD be fixed (maxBequest)",
            round_to=0,
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_annual",
        path="financial.spending.year0.today",
        label="Annual\nspending",
        fmt="currency",
        aggregates=["mean", "median", "p10", "p90"],
        description="Annual spending level",
        value_series_fn=make_spending_series_fn(
            objective_key="objective",
            objective_value="maxBequest",
            invariant_msg="Annual spending is fixed by user (objective=maxBequest)",
            violation_msg="Annual spending SHOULD be fixed (objective=maxBequest)",
            round_to=0,
        ),
    )
)

# =========================================================
# OVERRIDES (unchanged)
# =========================================================


def overrides_series_fn(values, raw, rows):
    clean = [v for v in raw if v]
    if not clean:
        return "-"
    unique = list({tuple(sorted(d.items())): d for d in clean}.values())
    if len(unique) == 1:
        return format_value(unique[0], "overrides")
    return f"{len(unique)} distinct override sets"


register_metric(
    MetricSpec(
        key="run_specific_overrides",
        label="Run-specific\noverrides",
        align="left",
        compute_fn=lambda d: d.get("run_specific_overrides"),
        fmt="overrides",
        dtype=dict,
        description="Overrides applied to this run",
        value_series_fn=overrides_series_fn,
    )
)

register_metric(
    MetricSpec(
        key="common_overrides",
        label="Common\noverrides",
        align="left",
        compute_fn=lambda d: d.get("run_common_overrides"),
        fmt="overrides",
        dtype=dict,
        description="Overrides applied to this run",
        value_series_fn=overrides_series_fn,
    )
)


register_metric(
    MetricSpec(
        key="has_overrides",
        label="Has\noverrides",
        align="left",
        compute_fn=lambda d: bool(d.get("run_specific_overrides")),
        dtype=str,
        description="Indicates presence of overrides",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(bool(v), "Overrides are present", "No overrides applied")
        ),
    )
)

register_metric(
    MetricSpec(
        key="has_overrides_display",
        label="Has\noverrides",
        align="center",
        compute_fn=lambda d: "Yes" if d.get("run_specific_overrides") else "-",
        dtype=str,
        description="Display indicator for overrides",
        value_series_fn=wrap_value_fn(
            lambda v, _: "Overrides applied" if v == "Yes" else "No overrides"
        ),
    )
)

# =========================================================
# INPUT (TOML)
# =========================================================

register_metric(
    MetricSpec(
        key="rates_method",
        path="_inputs.rates_selection.method",
        label="Rates Method",
        dtype=str,
        align="left",
        description="Method used to generate return scenarios",
        value_series_fn=wrap_value_fn(lambda v, _: f"Returns generated using '{v}' method"),
    )
)

register_metric(
    MetricSpec(
        key="rates_from",
        path="_inputs.rates_selection.from",
        label="From",
        dtype=int,
        description="Start year for historical data",
        value_series_fn=wrap_value_fn(lambda v, _: f"Data begins in {v}"),
    )
)

register_metric(
    MetricSpec(
        key="rates_to",
        path="_inputs.rates_selection.to",
        label="To",
        dtype=int,
        description="End year for historical data",
        value_series_fn=wrap_value_fn(lambda v, _: f"Data ends in {v}"),
    )
)

register_metric(
    MetricSpec(
        key="rates_values",
        path="_inputs.rates_selection.values",
        label="Rates values",
        dtype=list,
        align="left",
        description="static rates values for User method",
        value_series_fn=wrap_value_fn(lambda v, _: f"Static rates input for '{v}' method"),
    )
)


register_metric(
    MetricSpec(
        key="objective",
        path="_inputs.optimization_parameters.objective",
        label="Objective",
        dtype=str,
        description="Optimization objective",
        value_series_fn=wrap_value_fn(lambda v, _: f"Objective is '{v}'"),
    )
)

# =========================================================
# FINANCIAL (ADDITIONAL)
# =========================================================

register_metric(
    MetricSpec(
        key="taxes",
        path="financial.taxes.total.today",
        label="Taxes",
        fmt="currency",
        aggregates=["mean"],
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Total taxes paid: {format_value(v, 'currency')}"
        ),
    )
)

register_metric(
    MetricSpec(
        key="roth",
        path="financial.roth.total.today",
        label="Roth",
        fmt="currency",
        aggregates=["mean"],
        value_series_fn=wrap_value_fn(lambda v, _: f"Roth balance: {format_value(v, 'currency')}"),
    )
)


# =========================================================
# RISK — OUTCOME (CRITICAL)
# =========================================================

register_metric(
    MetricSpec(
        key="risk",
        path="risk.outcome.classification.risk_level",
        label="Risk",
        dtype=str,
        value_series_fn=wrap_value_fn(lambda v, _: f"Risk classification: {v}"),
    )
)

register_metric(
    MetricSpec(
        key="ending_assets",
        path="risk.outcome.assets.final_today",
        label="Ending Assets",
        fmt="currency",
        aggregates=["mean", "median", "p10", "p90"],
        value_series_fn=wrap_value_fn(lambda v, _: f"Final assets: {format_value(v, 'currency')}"),
    )
)

register_metric(
    MetricSpec(
        key="min_cushion",
        path="risk.outcome.cushion.min_cushion_ratio",
        label="Min Cushion",
        fmt="percent2",
        aggregates=["mean"],
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Minimum cushion: {format_value(v, 'percent2')}"
        ),
        description=(
            "Minimum asset cushion relative to required spending. "
            "Measures how close the plan comes to financial exhaustion."
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
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Worst drawdown: {format_value(v, 'percent2')}"
        ),
        description=(
            "Largest percentage decline in portfolio value from peak to trough. "
            "Captures market risk exposure."
        ),
    )
)

register_metric(
    MetricSpec(
        key="terminal_ratio",
        path="risk.outcome.terminal.spending_to_assets_ratio",
        label="Terminal S/A",
        fmt="percent2",
        aggregates=["mean"],
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Terminal spending/assets ratio: {format_value(v, 'percent2')}"
        ),
        description=(
            "Final assets divided by final spending requirement. "
            "Values >1 indicate surplus; values near 0 indicate depletion risk."
        ),
    )
)


# =========================================================
# DEPLETION (FAILURE SIGNAL)
# =========================================================

register_metric(
    MetricSpec(
        key="depleted",
        path="risk.outcome.depletion.depleted",
        label="Depleted",
        dtype=bool,
        value_series_fn=wrap_value_fn(
            lambda v, _: "Portfolio depleted" if v else "No depletion occurred"
        ),
    )
)

register_metric(
    MetricSpec(
        key="years_to_depletion",
        path="risk.outcome.depletion.years_to_depletion",
        label="Years to Depletion",
        fmt="int",
        aggregates=["mean"],
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Depletion occurs after {v} years" if v is not None else "-"
        ),
    )
)


# =========================================================
# SCENARIO DIAGNOSTICS (WHY IT FAILED)
# =========================================================

register_metric(
    MetricSpec(
        key="severity",
        path="risk.scenario.severity_score",
        label="Scenario Severity",
        fmt="float2",
        aggregates=["mean"],
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Scenario severity score: {format_value(v, 'float2')}"
        ),
    )
)

register_metric(
    MetricSpec(
        key="return_avg",
        path="risk.scenario.returns.avg",
        label="Avg Return",
        fmt="percent2",
        aggregates=["mean"],
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Average return: {format_value(v, 'percent2')}"
        ),
    )
)

register_metric(
    MetricSpec(
        key="return_worst",
        path="risk.scenario.returns.min",
        label="Worst Return",
        fmt="percent2",
        aggregates=["mean"],
        value_series_fn=wrap_value_fn(lambda v, _: f"Worst return: {format_value(v, 'percent2')}"),
    )
)

register_metric(
    MetricSpec(
        key="inflation_avg",
        path="risk.scenario.inflation.avg",
        label="Avg Inflation",
        fmt="percent2",
        aggregates=["mean"],
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Average inflation: {format_value(v, 'percent2')}"
        ),
    )
)

register_metric(
    MetricSpec(
        key="scenario_type",
        path="risk.scenario.classification.scenario_type",
        label="Risk scenario",
        dtype=str,
        align="left",
        value_series_fn=wrap_value_fn(lambda v, _: f"Scenario type: {v}"),
    )
)


# =========================================================
# COMPLEXITY (SECONDARY — DEBUGGING)
# =========================================================

register_metric(
    MetricSpec(
        key="num_vars",
        path="complexity.num_decision_variables",
        label="# Vars",
        fmt="int",
        aggregates=["mean"],
        value_series_fn=wrap_value_fn(lambda v, _: f"{v} decision variables"),
    )
)

register_metric(
    MetricSpec(
        key="num_constraints",
        path="complexity.num_constraints",
        label="# Constraints",
        fmt="int",
        aggregates=["mean"],
        value_series_fn=wrap_value_fn(lambda v, _: f"{v} constraints"),
    )
)


# =========================================================
# BASE TIMESERIES
# =========================================================

register_metric(
    MetricSpec(
        key="spending_series",
        label="Spending Series",
        path="financial.timeseries.spending.today_by_year",
        dtype=list,
        is_timeseries=True,
        description="Annual spending path (today dollars)",
    )
)


# =========================================================
# SPENDING PROFILE
# =========================================================

register_metric(
    MetricSpec(
        key="spending_min",
        label="Min Spending",
        fmt="currency",
        compute_fn=lambda r: (min(r["spending_series"]) if r.get("spending_series") else None),
        aggregates=["mean", "median", "p10"],
        description=(
            "Lowest annual spending observed in the simulation. "
            "Represents the worst lifestyle outcome experienced."
        ),
    )
)


register_metric(
    MetricSpec(
        key="spending_max",
        label="Max Spending",
        fmt="currency",
        compute_fn=lambda r: (max(r["spending_series"]) if r.get("spending_series") else None),
        aggregates=["mean", "p90"],
    )
)


register_metric(
    MetricSpec(
        key="spending_drop_pct",
        label="Max Drop",
        fmt="percent2",
        compute_fn=lambda r: (
            (r["spending_annual"] - min(r["spending_series"])) / r["spending_annual"]
            if r.get("spending_series") and r.get("spending_annual")
            else None
        ),
        aggregates=["mean", "p90"],
        description=(
            "Maximum percentage drop from baseline spending. "
            "Measures how much lifestyle must be reduced during stress scenarios."
        ),
    )
)


# =========================================================
# SLACK METRICS
# =========================================================

register_metric(
    MetricSpec(
        key="max_feasible_slack",
        label="Max Slack",
        fmt="percent2",
        compute_fn=lambda r: (
            (r["spending_annual"] - r["minimum_spending"]) / r["spending_annual"]
            if (
                r.get("spending_annual") is not None
                and r.get("minimum_spending") is not None
                and r["spending_annual"] != 0
            )
            else None
        ),
        aggregates=["mean"],
        description=(
            "Maximum spending reduction the plan can tolerate while remaining feasible. "
            "Represents available flexibility buffer."
        ),
    )
)

register_metric(
    MetricSpec(
        key="observed_slack_required",
        label="Slack Required",
        fmt="percent2",
        compute_fn=lambda r: (
            (r["spending_annual"] - min(r["spending_series"])) / r["spending_annual"]
            if r.get("spending_series") and r.get("spending_annual")
            else None
        ),
        aggregates=["mean", "p90"],
        description=(
            "Percentage reduction in spending required to maintain feasibility. "
            "Indicates how much flexibility is needed under adverse conditions."
        ),
    )
)


register_metric(
    MetricSpec(
        key="slack_feasible",
        label="Slack OK",
        dtype=bool,
        compute_fn=lambda r: (
            r.get("observed_slack_required") <= r.get("max_feasible_slack")
            if (
                r.get("observed_slack_required") is not None
                and r.get("max_feasible_slack") is not None
            )
            else None
        ),
        description=(
            "True if required spending reductions are within feasible limits. "
            "False indicates the plan cannot adapt sufficiently under stress."
        ),
    )
)

# =========================================================
# BEHAVIORAL METRIC (VERY USEFUL)
# =========================================================

register_metric(
    MetricSpec(
        key="years_below_minimum",
        label="Years < Min",
        fmt="int",
        compute_fn=lambda r: (
            sum(1 for v in r["spending_series"] if v < r["minimum_spending"])
            if r.get("spending_series") and r.get("minimum_spending")
            else None
        ),
        aggregates=["mean", "p90"],
        description=(
            "Number of years spending falls below minimum_spending. "
            "Captures frequency of lifestyle shortfall across the plan horizon."
        ),
    )
)


register_metric(
    MetricSpec(
        key="hard_fail",
        label="Hard Fail",
        dtype=int,
        fmt="int",  # default fallback (used only if no aggregate override)
        aggregates=[
            ("cnt_true", "int"),  # number of failed trials
            ("pct", "percent"),  # probability of failure
        ],
        compute_fn=lambda r: (
            0 if r.get("status") == "solved" else 1 if r.get("status") is not None else None
        ),
        description="Indicator that LP solver failed (1=fail, 0=success)",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Failure occurred", "No failure")
        ),
    )
)


def _soft_fail_details(r):
    series = r.get("spending_series")
    min_spend = r.get("minimum_spending")

    if series is None or len(series) == 0 or min_spend is None:
        return None

    inputs = r.get("_inputs", {}).get("risk_analysis", {}) or {}

    consec_thresh = inputs.get("soft_fail_consecutive_years_threshhold", 5)
    total_thresh = inputs.get("soft_fail_total_years_threshhold", 5)
    ratio_thresh = inputs.get("soft_fail_min_spending_ratio", 0.8)

    below = [v < min_spend for v in series]

    total_years = sum(below)

    max_consec = 0
    cur = 0
    for b in below:
        if b:
            cur += 1
            max_consec = max(max_consec, cur)
        else:
            cur = 0

    min_val = min(series)
    ratio = min_val / min_spend if min_spend else None
    severe = ratio is not None and ratio < ratio_thresh

    trigger_duration = total_years >= total_thresh
    trigger_consec = max_consec >= consec_thresh
    trigger_severity = severe

    fail = trigger_duration or trigger_consec or trigger_severity

    return {
        "fail": int(fail),
        "total_years": total_years,
        "max_consec": max_consec,
        "severe": severe,
        "min_val": min_val,
        "min_spend": min_spend,
        "ratio": ratio,
        "total_thresh": total_thresh,
        "consec_thresh": consec_thresh,
        "ratio_thresh": ratio_thresh,
        "trigger_duration": trigger_duration,
        "trigger_consec": trigger_consec,
        "trigger_severity": trigger_severity,
    }


register_metric(
    MetricSpec(
        key="soft_fail_total_years",
        label="Soft Fail Years",
        dtype=int,
        aggregates=["mean", "p90"],
        compute_fn=lambda r: (_soft_fail_details(r) or {}).get("total_years"),
        description=(
            "Total number of years spending falls below minimum_spending. "
            "Computed per trial from spending_series vs minimum_spending. "
            "Higher values indicate prolonged lifestyle shortfall."
        ),
    )
)

register_metric(
    MetricSpec(
        key="soft_fail_max_consec",
        label="Soft Fail Consec",
        dtype=int,
        aggregates=["mean", "p90"],
        compute_fn=lambda r: (_soft_fail_details(r) or {}).get("max_consec"),
        description=(
            "Maximum consecutive years spending remains below minimum_spending. "
            "Captures sequence risk and sustained financial stress. "
            "High values indicate long uninterrupted hardship periods."
        ),
    )
)

register_metric(
    MetricSpec(
        key="soft_fail_ratio",
        label="Soft Fail Ratio",
        dtype=float,
        fmt="percent",
        aggregates=["mean", "p10"],
        compute_fn=lambda r: (_soft_fail_details(r) or {}).get("ratio"),
        description=(
            "Worst-case spending level as a fraction of minimum_spending "
            "(min(spending_series) / minimum_spending). "
            "Lower values indicate deeper shortfalls. "
            "p10 highlights downside severity across trials."
        ),
    )
)


def _compute_soft_fail(r):
    d = _soft_fail_details(r)
    if d is None:
        return None

    # 🔥 store details for later explain
    r["_soft_fail_details"] = d

    return d["fail"]


register_metric(
    MetricSpec(
        key="soft_fail",
        label="Soft Fail",
        dtype=int,
        fmt=None,  # let aggregates control formatting
        aggregates=["cnt_true", "pct"],
        compute_fn=lambda r: (
            (d := _soft_fail_details(r))["fail"]
            if (d := _soft_fail_details(r)) is not None
            else None
        ),
        description="Behavioral failure based on duration, frequency, or severity thresholds",
        value_series_fn=wrap_value_fn(
            lambda v, r: (
                f"{format_value(r.get('soft_fail_cnt_true'), 'int')}/"
                f"{format_value(r.get('soft_fail_cnt_true_n'), 'int')} failed | "
                f"avg {format_value(r.get('soft_fail_total_years_mean'), 'int')} yrs, "
                f"{format_value(r.get('soft_fail_max_consec_mean'), 'int')} consec, "
                f"min {format_value(r.get('soft_fail_ratio_p10'), 'percent')} | "
                f"trigger: "
                f"{'duration ' if r.get('soft_fail_trigger_duration_cnt_true') else ''}"
                f"{'consecutive ' if r.get('soft_fail_trigger_consec_cnt_true') else ''}"
                f"{'severity' if r.get('soft_fail_trigger_severity_cnt_true') else ''}"
            )
            if r.get("soft_fail_cnt_true") is not None
            else "-"
        ),
    )
)


register_metric(
    MetricSpec(
        key="soft_fail_trigger",
        label="Soft Fail Trigger",
        dtype=str,
        aggregates=None,  # 🔥 IMPORTANT: no aggregation
        compute_fn=lambda r: (
            "+".join(
                t
                for t, flag in [
                    ("duration", d["trigger_duration"]),
                    ("consecutive", d["trigger_consec"]),
                    ("severity", d["trigger_severity"]),
                ]
                if flag
            )
            if (d := _soft_fail_details(r)) and d["fail"]
            else None
        ),
        description="Triggers for soft failure (trial-level only)",
    )
)


register_metric(
    MetricSpec(
        key="soft_fail_trigger_duration",
        label="Fail: Duration",
        dtype=int,
        aggregates=["cnt_true", "pct"],
        compute_fn=lambda r: (1 if (d := _soft_fail_details(r)) and d["trigger_duration"] else 0)
        if _soft_fail_details(r)
        else None,
        description=(
            "Soft failure triggered by total years below minimum_spending "
            "exceeding threshold (soft_fail_total_years_threshhold). "
            "Indicates long-term underfunding."
        ),
    )
)

register_metric(
    MetricSpec(
        key="soft_fail_trigger_consec",
        label="Fail: Consecutive",
        dtype=int,
        aggregates=["cnt_true", "pct"],
        compute_fn=lambda r: (1 if (d := _soft_fail_details(r)) and d["trigger_consec"] else 0)
        if _soft_fail_details(r)
        else None,
        description=(
            "Soft failure triggered by consecutive years below minimum_spending "
            "exceeding threshold (soft_fail_consecutive_years_threshhold). "
            "Represents sustained financial stress."
        ),
    )
)

register_metric(
    MetricSpec(
        key="soft_fail_trigger_severity",
        label="Fail: Severity",
        dtype=int,
        aggregates=["cnt_true", "pct"],
        compute_fn=lambda r: (1 if (d := _soft_fail_details(r)) and d["trigger_severity"] else 0)
        if _soft_fail_details(r)
        else None,
        description=(
            "Soft failure triggered by spending dropping below a critical ratio "
            "of minimum_spending (soft_fail_min_spending_ratio). "
            "Captures extreme lifestyle degradation."
        ),
    )
)


register_metric(
    MetricSpec(
        key="total_fail",
        label="Total Fail",
        dtype=int,
        fmt=None,
        aggregates=["cnt_true", "pct"],
        compute_fn=lambda r: (
            1
            if (
                r.get("hard_fail") == 1
                or ((d := _soft_fail_details(r)) is not None and d["fail"] == 1)
            )
            else 0
        )
        if r.get("hard_fail") is not None
        else None,
        description="Total failures: hard (insolvency) or soft (lifestyle breach)",
        value_series_fn=wrap_value_fn(
            lambda v, r: (
                f"{format_value(r.get('total_fail_cnt_true'), 'int')}/"
                f"{format_value(r.get('total_fail_cnt_true_n'), 'int')} failed "
                f"({format_value(r.get('total_fail_pct'), 'percent')})"
            )
            if r.get("total_fail_cnt_true") is not None
            else "-"
        ),
    )
)
