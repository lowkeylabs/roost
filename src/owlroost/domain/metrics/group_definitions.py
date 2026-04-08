from .group_registry import register_group

# =========================================================
# CORE OUTCOMES
# =========================================================

register_group(
    "core_outcomes_trial",
    [
        "bequest",
        "ending_assets",
    ],
    description="Core financial outcomes for a single trial",
)

register_group(
    "goal",
    [
        "goal",
    ],
    description="Optimization goals",
)


register_group(
    "core_outcomes_run",
    [
        ("spending_total", "median"),
        ("taxes_total", "median", {"show_if": "is_pivot"}),
        ("bequest", "median", {"show_if": "is_pivot"}),
        # ("ending_assets", "median",{"showif","is_pivot"}),
    ],
    description="Core financial outcomes aggregated at the run level",
)

register_group(
    "spending_profile",
    [
        ("spending_now", "median"),
        ("spending_early", "median", {"show_if": "is_table"}),
        ("spending_late", "median"),
        ("spending_survivor_ratio", "mean"),
        ("spending_final", "median"),
    ],
    description="Spending levels across lifecycle phases (early vs late / survivor)",
    default_opts={"show_if": "is_pivot"},
)


register_group(
    "outcomes",
    [
        ("spending_now", "median"),
        ("spending_total", "median"),
        ("bequest", "median"),
    ],
    description="Core financial outcomes (primary decision signals)",
)

register_group(
    "lifestyle",
    [
        "acceptable_spending",
        ("spending_ratio_to_acceptable_min", "mean", {"show_if": ["is_table", "is_pivot"]}),
        ("years_below_acceptable", "mean"),
        ("consecutive_years_below_acceptable", "mean"),
        ("years_below_acceptable", "p90"),
        ("consecutive_years_below_acceptable", "p90"),
        ("spending_stress_flag", "ratio"),
    ],
    description="Lifestyle quality relative to acceptable spending (adjusted for household size via xi_n)",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "safety",
    [
        "minimum_spending",
        ("spending_ratio_to_minimum_min", "mean", {"show_if": ["is_table", "is_pivot"]}),
        ("years_below_minimum", "mean"),
        ("consecutive_years_below_minimum", "mean"),
        ("years_below_minimum", "p90"),
        ("consecutive_years_below_minimum", "p90"),
        ("floor_breach", "ratio"),
    ],
    description="Safety relative to users-input value of minimum spending.",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "risk_summary",
    [
        "overall_risk",
        ("scenario_severity", "mean"),
        ("depleted", "ratio"),
        ("risk_flag_count", "mean"),
        "risk_flags",
        "risk_reconciliation",
    ],
    description="High-level risk summary combining scenario and outcome signals",
    default_opts={"show_if": "is_pivot"},
)

# =========================================================
# SPENDING — TARGET (Goal Performance)
# =========================================================

register_group(
    "target_performance",
    [
        ("spending_ratio_min", "mean"),
        ("spending_shortfall", "mean"),
        ("years_under_target", "mean"),
        ("spending_ratio_p10", "mean"),
        ("spending_ratio_median", "mean"),
        ("spending_ratio_mean", "mean"),
        ("spending_ratio_std", "mean"),
        ("spending_shortfall", "p90"),
        ("years_under_target", "p90"),
        ("required_slack", "mean"),
        ("required_slack", "p90"),
    ],
    description="Performance relative to target spending",
)

# =========================================================
# SPENDING — ACCEPTABLE (Lifestyle Tolerance)
# =========================================================

register_group(
    "acceptable_lifestyle",
    [
        "minimum_spending",
        "acceptable_spending",
        ("spending_ratio_to_acceptable_min", "mean", {"show_if": ["is_table", "is_pivot"]}),
        ("years_below_acceptable", "mean"),
        ("consecutive_years_below_acceptable", "mean"),
        ("years_below_acceptable", "p90"),
        ("consecutive_years_below_acceptable", "p90"),
        ("spending_stress_flag", "count_ratio"),
        ("spending_stress_flag", "ratio"),
    ],
    description="Behavior relative to acceptable lifestyle spending",
    default_opts={"show_if": "is_pivot"},
)

# =========================================================
# SPENDING — MINIMUM (Floor Safety)
# =========================================================

register_group(
    "minimum_safety",
    [
        ("spending_ratio_to_minimum_min", "mean", {"show_if": ["is_table", "is_pivot"]}),
        ("years_below_minimum", "mean"),
        ("years_below_minimum", "p90"),
        ("floor_breach", "count_ratio"),
        ("floor_breach", "ratio"),
    ],
    description="Safety relative to minimum spending floor",
    default_opts={"show_if": "is_pivot"},
)

# =========================================================
# SPENDING — TRIAL DETAIL
# =========================================================

register_group(
    "trial_spending_detail",
    [
        "spending_ratio_min",
        "spending_ratio_to_acceptable_min",
        "spending_ratio_to_minimum_min",
        "years_under_target",
        "years_below_acceptable",
        "years_below_minimum",
        "spending_stress_flag",
    ],
    description="Detailed per-trial spending stress metrics",
)

# =========================================================
# PORTFOLIO RISK
# =========================================================

register_group(
    "portfolio_risk",
    [
        "outcome_risk",
        ("min_cushion", "mean"),
        ("worst_drawdown", "mean"),
        ("terminal_ratio", "mean"),
        ("terminal_assets_to_spending", "mean"),
    ],
    description="Asset-based risk and sustainability metrics",
)

register_group(
    "portfolio_risk_trial",
    [
        "min_cushion",
        "worst_drawdown",
        "terminal_ratio",
        "terminal_assets_to_spending",
    ],
    description="Per-trial asset-based risk metrics",
)

# =========================================================
# FEASIBILITY
# =========================================================

register_group(
    "feasibility",
    [
        ("solver_fail", "cnt_true"),
        ("solver_fail", "pct"),
    ],
    description="Solver feasibility and failure rates",
)

# =========================================================
# STRUCTURE / CONTEXT
# =========================================================

register_group(
    "run_identity",
    [
        ("case_name", {"show_if": ["is_table", "is_pivot"]}),
        ("run_id_compact", {"show_if": "is_table"}),
        "case",
        "experiment",
        "run",
        ("trial", "cnt", {"show_if": ["is_table", "is_pivot"]}),
    ],
    description="Run identify info",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "run_structure",
    [
        ("rates", {"show_if": "is_table"}),
        "rates_method",
        "rates_values",
        "objective",
    ],
    description="Key solver parameters",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "overrides",
    [
        ("run_profile", {"show_if": ["is_pivot", "is_table"]}),
        "run_specific_overrides",
        "common_overrides",
    ],
    description="Overrides for this run",
    default_opts={"show_if": "is_pivot"},
)

# =========================================================
# RUN DASHBOARD PROFILE
# =========================================================

# =========================================================
# RUN DASHBOARD — PROFILE FLAGS (PIVOT)
# =========================================================

register_group(
    "run_profile_flags",
    [
        "is_ss_experiment",
        "is_spending_slack",
        "is_sor_experiment",
        "is_roth_strategy",
        "has_overrides",
    ],
    description="Detailed run classification flags (pivot only)",
)


# =========================================================
# RUN DASHBOARD — CORE (TABLE-FIRST SIGNALS)
# =========================================================

register_group(
    "run_dashboard_core",
    [
        "run_profile",
        "bad_run_flag",
        "needs_attention",
        ("solver_fail", "pct"),
        ("spending_annual", "median"),
        ("spending_ratio_min", "mean"),
    ],
    description="Minimal decision signals for run triage (table view)",
)

# =========================================================
# RUN DASHBOARD — OUTCOMES (PIVOT)
# =========================================================

register_group(
    "run_outcomes_pivot",
    [
        ("ending_assets", "median"),
        ("bequest", "median"),
    ],
    description="Expanded financial outcomes for pivot comparison",
)

# =========================================================
# RUN DASHBOARD — RISK (PIVOT)
# =========================================================

register_group(
    "run_risk_pivot",
    [
        "overall_risk",
        "outcome_risk",
        ("depleted", "ratio"),
        ("floor_breach", "ratio"),
        ("scenario_severity", "mean"),
        ("min_cushion", "mean"),
        ("terminal_ratio", "mean"),
    ],
    description="Risk summary and edge-of-failure indicators",
    default_opts={"show_if": "is_pivot"},
)
