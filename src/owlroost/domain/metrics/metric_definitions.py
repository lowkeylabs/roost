from .metric_registry import register_metric
from .metric_spec import MetricSpec

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
        explain_value_static="Identifies which case this result belongs to",
    )
)

register_metric(
    MetricSpec(
        key="experiment",
        label="Exp",
        aggregates=["cnt"],
        description="Experiment identifier grouping multiple runs",
        explain_value_static="Used to group runs under a shared configuration",
    )
)

register_metric(
    MetricSpec(
        key="run",
        label="Run",
        aggregates=["cnt"],
        description="Run identifier within an experiment",
        explain_value_static="Each run represents a distinct parameterization",
    )
)

register_metric(
    MetricSpec(
        key="trial",
        label="Trial",
        dtype=int,
        aggregates=["cnt"],
        description="Trial index within a run",
        explain_value_static="Each trial is one simulated scenario realization",
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
        explain_value_static="Ensures deterministic scenario generation",
    )
)

# =========================================================
# STATUS / CORE
# =========================================================

register_metric(
    MetricSpec(
        key="status",
        path="run_status.status",
        label="Status",
        dtype=str,
        align="left",
        description="Outcome status of the optimization run",
        explain_value_static="Indicates whether the solver succeeded or failed",
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
        explain_value_static="Lower values indicate faster solve performance",
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
        explain_value_static="1 = solved successfully, 0 = failure",
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
        explain_value_static="1 = failure, 0 = success",
    )
)

register_metric(
    MetricSpec(
        key="failure_reason",
        path="run_status.failure_category",
        label="Failure Reason",
        dtype=str,
        description="Category of failure when optimization does not solve",
    )
)

register_metric(
    MetricSpec(
        key="is_failed",
        label="Failed?",
        dtype=bool,
        compute_fn=lambda d: d.get("status") == "failed",
        description="Boolean indicator of failure",
    )
)

register_metric(
    MetricSpec(
        key="is_solved",
        label="Solved?",
        dtype=bool,
        compute_fn=lambda d: d.get("status") == "solved",
        description="Boolean indicator of success",
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
        explain_value_static="Higher values indicate more leftover wealth",
    )
)

register_metric(
    MetricSpec(
        key="spending_total",
        path="financial.spending.total.today",
        label="Total\nSpending",
        fmt="currency",
        aggregates=["mean", "median", "p10", "p90"],
        description="Total lifetime spending",
        explain_value_static="Represents total consumption over the plan",
    )
)

register_metric(
    MetricSpec(
        key="spending_annual",
        path="financial.spending.year0.today",
        label="Annual\nspending",
        fmt="currency",
        aggregates=["mean", "median", "p10", "p90"],
        description="Annual spending over life of plan",
        explain_value_static="Represents amount spent annually, not including conversions, taxes, etc.",
    )
)

register_metric(
    MetricSpec(
        key="taxes",
        path="financial.taxes.total.today",
        label="Taxes",
        fmt="currency",
        aggregates=["mean"],
        description="Total taxes paid",
        explain_value_static="Reflects tax burden of the strategy",
    )
)

register_metric(
    MetricSpec(
        key="roth",
        path="financial.roth.total.today",
        label="Roth",
        fmt="currency",
        aggregates=["mean"],
        description="Total Roth balances or conversions",
        explain_value_static="Indicates tax-efficient positioning",
    )
)

# =========================================================
# RISK
# =========================================================

register_metric(
    MetricSpec(
        key="risk",
        path="risk.outcome.classification.risk_level",
        label="Risk",
        dtype=str,
        description="Risk classification of the outcome",
        explain_value_static="Categorizes outcome severity (safe, fragile, failure)",
    )
)

register_metric(
    MetricSpec(
        key="ending_assets",
        path="risk.outcome.assets.final_today",
        label="Ending Assets",
        fmt="currency",
        aggregates=["mean", "median", "p10", "p90"],
        description="Assets remaining at the end of the simulation",
        explain_value_static="Higher values indicate stronger outcomes",
    )
)

register_metric(
    MetricSpec(
        key="min_cushion",
        path="risk.outcome.cushion.min_cushion_ratio",
        label="Min Cushion",
        fmt="percent2",
        aggregates=["mean"],
        description="Minimum safety margin during the plan",
        explain_value_static="Lower values indicate higher risk of depletion",
    )
)

register_metric(
    MetricSpec(
        key="worst_drawdown",
        path="risk.outcome.drawdown.worst_drawdown_factor",
        label="Worst Drawdown",
        fmt="percent2",
        aggregates=["mean"],
        description="Maximum portfolio drawdown",
        explain_value_static="Captures downside volatility risk",
    )
)

register_metric(
    MetricSpec(
        key="terminal_ratio",
        path="risk.outcome.terminal.spending_to_assets_ratio",
        label="Terminal S/A",
        fmt="percent2",
        aggregates=["mean"],
        description="Spending-to-assets ratio at end of plan",
        explain_value_static="Higher values may indicate stress at horizon",
    )
)

# =========================================================
# DEPLETION
# =========================================================

register_metric(
    MetricSpec(
        key="depleted",
        path="risk.outcome.depletion.depleted",
        label="Depleted",
        dtype=bool,
        description="Whether assets were exhausted",
        explain_value_static="True indicates financial failure",
    )
)

register_metric(
    MetricSpec(
        key="years_to_depletion",
        path="risk.outcome.depletion.years_to_depletion",
        label="Years to Depletion",
        fmt="int",
        aggregates=["mean"],
        description="Time until assets are depleted",
        explain_value_static="Lower values indicate earlier failure",
    )
)

# =========================================================
# SCENARIO
# =========================================================

register_metric(
    MetricSpec(
        key="severity",
        path="risk.scenario.severity_score",
        label="Scenario Severity",
        fmt="float2",
        aggregates=["mean"],
        description="Severity of the economic scenario",
        explain_value_static="Higher values indicate worse conditions",
    )
)

register_metric(
    MetricSpec(
        key="return_avg",
        path="risk.scenario.returns.avg",
        label="Avg Return",
        fmt="percent2",
        aggregates=["mean"],
        description="Average return during the scenario",
        explain_value_static="Higher values indicate stronger markets",
    )
)

register_metric(
    MetricSpec(
        key="return_worst",
        path="risk.scenario.returns.min",
        label="Worst Return",
        fmt="percent2",
        aggregates=["mean"],
        description="Worst observed return in the scenario",
        explain_value_static="Captures downside shocks",
    )
)

register_metric(
    MetricSpec(
        key="inflation_avg",
        path="risk.scenario.inflation.avg",
        label="Avg Inflation",
        fmt="percent2",
        aggregates=["mean"],
        description="Average inflation rate",
        explain_value_static="Higher values reduce real purchasing power",
    )
)

register_metric(
    MetricSpec(
        key="scenario_type",
        path="risk.scenario.classification.scenario_type",
        label="Risk scenario",
        dtype=str,
        align="left",
        description="Classification of economic scenario",
    )
)

# =========================================================
# COMPLEXITY
# =========================================================

register_metric(
    MetricSpec(
        key="num_vars",
        path="complexity.num_decision_variables",
        label="# Vars",
        fmt="int",
        aggregates=["mean"],
        description="Number of decision variables in optimization",
    )
)

register_metric(
    MetricSpec(
        key="num_constraints",
        path="complexity.num_constraints",
        label="# Constraints",
        fmt="int",
        aggregates=["mean"],
        description="Number of constraints in optimization",
    )
)

# =========================================================
# OVERRIDES
# =========================================================


def _format_overrides(overrides: dict | None) -> str:
    if not overrides:
        return ""
    return "\n".join(f"{k}={v}" for k, v in sorted(overrides.items()))


register_metric(
    MetricSpec(
        key="run_overrides_display",
        label="Run-specific overrides",
        align="left",
        compute_fn=lambda d: _format_overrides(d.get("run_specific_overrides")),
        dtype=str,
        description="Overrides applied to this run",
    )
)

register_metric(
    MetricSpec(
        key="has_overrides",
        label="Has\noverrides",
        align="left",
        compute_fn=lambda d: True if len(d.get("run_specific_overrides")) > 0 else False,
        dtype=str,
        description="Indicates presence of overrides",
    )
)

register_metric(
    MetricSpec(
        key="has_overrides_display",
        label="Has\noverrides",
        align="center",
        compute_fn=lambda d: "Yes" if len(d.get("run_specific_overrides")) > 0 else "-",
        dtype=str,
        description="Display-friendly override indicator",
        explain_value_static="Alternate inputs were used for this run.",
    )
)
