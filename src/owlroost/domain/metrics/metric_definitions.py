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
