from .metric_registry import register_metric
from .metric_spec import MetricSpec

# =========================================================
# CONTEXT METRICS (from enrichment layer)
# =========================================================

register_metric(
    MetricSpec(
        key="case_name",
        label="Case name",
        dtype=str,
        align="left",
        is_invariant=True,
    )
)

register_metric(MetricSpec(key="experiment", label="Exp", is_invariant=True, aggregates=["cnt"]))

register_metric(MetricSpec(key="run", label="Run", is_invariant=True, aggregates=["cnt"]))


register_metric(MetricSpec(key="trial", label="Trial", dtype=int, aggregates=["cnt"]))

register_metric(
    MetricSpec(
        key="master_seed",
        label="Seed",
        compute_fn=lambda d: d.get("master_seed"),
        dtype=int,
        is_invariant=True,
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
    )
)

register_metric(
    MetricSpec(
        key="elapsed",
        path="timing.elapsed_seconds",
        label="Time (s)",
        fmt="float2",
        aggregates=["mean", "p90"],
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
    )
)

register_metric(
    MetricSpec(
        key="failure_reason",
        path="run_status.failure_category",
        label="Failure Reason",
        dtype=str,
    )
)

register_metric(
    MetricSpec(
        key="is_failed",
        label="Failed?",
        dtype=bool,
        compute_fn=lambda d: d.get("status") == "failed",
    )
)

register_metric(
    MetricSpec(
        key="is_solved",
        label="Solved?",
        dtype=bool,
        compute_fn=lambda d: d.get("status") == "solved",
    )
)

# =========================================================
# FINANCIAL (PRIMARY OUTCOMES)
# =========================================================

register_metric(
    MetricSpec(
        key="bequest",
        path="financial.bequest.total.today",
        label="Bequest",
        fmt="currency",
        aggregates=["mean", "median", "p10", "p90"],
    )
)

register_metric(
    MetricSpec(
        key="spending",
        path="financial.spending.total.today",
        label="Spending",
        fmt="currency",
        aggregates=["mean"],
    )
)

register_metric(
    MetricSpec(
        key="taxes",
        path="financial.taxes.total.today",
        label="Taxes",
        fmt="currency",
        aggregates=["mean"],
    )
)

register_metric(
    MetricSpec(
        key="roth",
        path="financial.roth.total.today",
        label="Roth",
        fmt="currency",
        aggregates=["mean"],
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
    )
)

register_metric(
    MetricSpec(
        key="ending_assets",
        path="risk.outcome.assets.final_today",
        label="Ending Assets",
        fmt="currency",
        aggregates=["mean", "median", "p10", "p90"],
    )
)

register_metric(
    MetricSpec(
        key="min_cushion",
        path="risk.outcome.cushion.min_cushion_ratio",
        label="Min Cushion",
        fmt="percent2",
        aggregates=["mean"],
    )
)

register_metric(
    MetricSpec(
        key="worst_drawdown",
        path="risk.outcome.drawdown.worst_drawdown_factor",
        label="Worst Drawdown",
        fmt="percent2",
        aggregates=["mean"],
    )
)

register_metric(
    MetricSpec(
        key="terminal_ratio",
        path="risk.outcome.terminal.spending_to_assets_ratio",
        label="Terminal S/A",
        fmt="percent2",
        aggregates=["mean"],
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
    )
)

register_metric(
    MetricSpec(
        key="years_to_depletion",
        path="risk.outcome.depletion.years_to_depletion",
        label="Years to Depletion",
        fmt="int",
        aggregates=["mean"],
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
    )
)

register_metric(
    MetricSpec(
        key="return_avg",
        path="risk.scenario.returns.avg",
        label="Avg Return",
        fmt="percent2",
        aggregates=["mean"],
    )
)

register_metric(
    MetricSpec(
        key="return_worst",
        path="risk.scenario.returns.min",
        label="Worst Return",
        fmt="percent2",
        aggregates=["mean"],
    )
)

register_metric(
    MetricSpec(
        key="inflation_avg",
        path="risk.scenario.inflation.avg",
        label="Avg Inflation",
        fmt="percent2",
        aggregates=["mean"],
    )
)

register_metric(
    MetricSpec(
        key="scenario_type",
        path="risk.scenario.classification.scenario_type",
        label="Risk scenario",
        dtype=str,
        align="left",
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
    )
)

register_metric(
    MetricSpec(
        key="num_constraints",
        path="complexity.num_constraints",
        label="# Constraints",
        fmt="int",
        aggregates=["mean"],
    )
)

# =========================================================
# OVERRIDES
# =========================================================


def _format_overrides(overrides: dict | None) -> str:
    if not overrides:
        return ""

    lines = [f"{k}={v}" for k, v in sorted(overrides.items())]
    return "\n".join(lines)


register_metric(
    MetricSpec(
        key="run_overrides_display",
        label="Run-specific overrides",
        align="left",
        compute_fn=lambda d: _format_overrides(d.get("run_specific_overrides")),
        dtype=str,
    )
)
