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
        ("spending_now", "median"),
        ("spending_total", "median"),
        ("bequest", "median"),
    ],
    description="Core financial outcomes aggregated at the run level",
)

register_group(
    "spending_profile",
    [
        ("spending_now", "median"),
        ("spending_early", "median"),
        ("spending_late", "median"),
        ("spending_survivor_ratio", "mean"),
        ("spending_final", "median"),
    ],
    description="Spending levels across lifecycle phases",
    default_opts={"show_if": "is_pivot"},
)


# =========================================================
# RISK GROUPS
# =========================================================

register_group(
    "lifestyle_spending_risk",
    [
        "lifestyle_spending",
        "lifestyle_spending_risk",
        ("spending_ratio_to_lifestyle_min", "mean"),
        ("spending_ratio_to_lifestyle_min", "p10"),
        ("years_below_lifestyle", "mean"),
        ("years_below_lifestyle", "p90"),
        ("consecutive_years_below_lifestyle", "mean"),
        ("consecutive_years_below_lifestyle", "p90"),
        ("lifestyle_stress_flag", "ratio"),
    ],
    description="Risk of failing to maintain lifestyle spending.",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "essential_spending_risk",
    [
        "essential_spending",
        "essential_spending_risk",
        ("spending_ratio_to_essential_min", "mean"),
        ("spending_ratio_to_essential_min", "p10"),
        ("years_below_essential", "mean"),
        ("years_below_essential", "p90"),
        ("consecutive_years_below_essential", "mean"),
        ("consecutive_years_below_essential", "p90"),
        ("essential_spending_breach", "ratio"),
    ],
    description="Risk of failing to meet essential spending.",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "depletion_risk",
    [
        ("depleted", "ratio"),
        ("min_cushion", "mean"),
        ("terminal_ratio", "mean"),
    ],
    description="Risk of asset depletion and end-of-horizon resilience.",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "risk_summary",
    [
        "overall_risk",
        ("scenario_severity", "mean"),
        ("depleted", "ratio"),
        "risk_flags",
        "risk_signals",
        "risk_interpretation",
    ],
    description="High-level risk summary",
    default_opts={"show_if": "is_pivot"},
)


# =========================================================
# SPENDING — TARGET PERFORMANCE
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
    description="Performance relative to baseline spending",
    default_opts={"show_if": "is_pivot"},
)


# =========================================================
# SPENDING — LIFESTYLE
# =========================================================

register_group(
    "lifestyle_spending",
    [
        "essential_spending",
        "lifestyle_spending_input",
        ("spending_ratio_to_lifestyle_min", "mean"),
        ("years_below_lifestyle", "mean"),
        ("consecutive_years_below_lifestyle", "mean"),
        ("years_below_lifestyle", "p90"),
        ("consecutive_years_below_lifestyle", "p90"),
        ("lifestyle_stress_flag", "count_ratio"),
        ("lifestyle_stress_flag", "ratio"),
    ],
    description="Behavior relative to lifestyle spending target",
    default_opts={"show_if": "is_pivot"},
)


# =========================================================
# SPENDING — ESSENTIAL
# =========================================================

register_group(
    "essential_spending",
    [
        ("spending_ratio_to_essential_min", "mean"),
        ("years_below_essential", "mean"),
        ("years_below_essential", "p90"),
        ("essential_spending_breach", "count_ratio"),
        ("essential_spending_breach", "ratio"),
    ],
    description="Safety relative to essential spending floor",
    default_opts={"show_if": "is_pivot"},
)


# =========================================================
# SPENDING — TRIAL DETAIL
# =========================================================

register_group(
    "trial_spending_detail",
    [
        "spending_ratio_min",
        "spending_ratio_to_lifestyle_min",
        "spending_ratio_to_essential_min",
        "years_under_target",
        "years_below_lifestyle",
        "years_below_essential",
        "lifestyle_stress_flag",
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
    description="Asset-based risk metrics",
    default_opts={"show_if": "is_pivot"},
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
    default_opts={"show_if": "is_pivot"},
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
        ("trials_requested", {"show_if": ["is_table", "is_pivot"]}),
        ("trials_completed", {"show_if": ["is_table", "is_pivot"]}),
        ("signature", {"show_if": "is_pivot"}),
    ],
    description="Run identity info",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "run_identity_trial",
    [
        ("case_name", {"show_if": "is_pivot"}),
        ("run_id_compact", {"show_if": "is_table"}),
        "case",
        "experiment",
        "run",
        ("trial", "cnt", {"show_if": ["is_table", "is_pivot"]}),
        ("signature", {"show_if": "is_pivot"}),
    ],
    description="Run identity info",
    default_opts={"show_if": "is_pivot"},
)


register_group(
    "run_structure",
    [
        ("input_rates", {"show_if": "is_table"}),
        "input_rates_method",
        "input_rates_values",
    ],
    description="Key solver parameters",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "overrides",
    [
        ("run_variation_profile", {"show_if": ["is_pivot", "is_table"]}),
        "run_specific_overrides",
        "common_overrides",
    ],
    description="Overrides for this run",
    default_opts={"show_if": "is_pivot"},
)

# =========================================================
# SOCIAL SECURITY
# =========================================================

register_group(
    "social_security",
    [
        "ss_input_p1",
        "ss_input_p2",
        "is_ss_experiment",
        ("ss_age_p1", "median"),
        ("ss_age_p1", "p10"),
        ("ss_age_p1", "p90"),
        ("ss_age_p2", "median"),
        ("ss_age_p2", "p10"),
        ("ss_age_p2", "p90"),
    ],
    description="Social Security claiming strategy and optimization outcomes.",
    default_opts={"show_if": "is_pivot"},
)


# =========================================================
# RATE ENVIRONMENT (ALIGNED WITH rates.py)
# =========================================================

register_group(
    "rates_characterization",
    [
        ("real_return", "median"),
        ("real_return_std", "median"),
        ("inflation_avg", "median"),
    ],
    description="Full-horizon real return, volatility, and inflation.",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "rates_input",
    [
        "input_rates_method",
        "input_rates_values",
    ],
    description="Rate generation method and inputs.",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "rates_early",
    [
        ("early_real_cagr", "median"),
        ("early_real_cagr", "p10"),
        ("early_real_mean", "median"),
        ("early_min_year", "median"),
    ],
    description="Early sequence-of-returns characteristics.",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "rates_full",
    [
        ("real_return", "median"),
        ("real_return", "p10"),
        ("real_return_std", "median"),
        ("inflation_avg", "median"),
    ],
    description="Full-horizon return characteristics.",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "rates_cross",
    [
        ("early_vs_full_real_gap", "median"),
        ("early_vs_full_real_gap", "p10"),
    ],
    description="Comparison between early-period and full-horizon returns.",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "rates_regime_summary",
    [
        "dominant_rate_regime",
    ],
    description="Dominant economic regime classification.",
    default_opts={"show_if": "is_pivot"},
)

register_group(
    "rates_regime_distribution",
    [
        "regime_stagflation_pct",
        "regime_deflation_pct",
        "regime_moderate_pct",
        "regime_goldilocks_pct",
        "regime_inflation_boom_pct",
    ],
    description="Distribution of economic regimes across trials.",
    default_opts={"show_if": "is_pivot"},
)


# =========================================================
# AUDIT
# =========================================================

register_group(
    "audit",
    [
        # -------------------------------------------------
        # Outcome counts (primary)
        # -------------------------------------------------
        ("trial_completeness"),
        ("solved", "sum", {"show_if": "is_pivot"}),
        ("timeout", "sum"),
        ("error", "sum"),
        # Ratios (cleaner than separate rate metrics)
        ("solved", "pct", {"show_if": "is_pivot"}),
        ("timeout", "pct", {"show_if": "is_pivot"}),
        ("error", "pct", {"show_if": "is_pivot"}),
        # -------------------------------------------------
        # Execution configuration
        # -------------------------------------------------
        ("solver"),
        ("trial_jobs"),
        ("worker_timeout"),
        # -------------------------------------------------
        # Timing (per-trial distribution)
        # -------------------------------------------------
        ("elapsed_seconds", "median", {"show_if": "is_pivot"}),
        ("elapsed_seconds", "p10", {"show_if": "is_pivot"}),
        ("elapsed_seconds", "p90", {"show_if": "is_pivot"}),
        # -------------------------------------------------
        # Run-level performance
        # -------------------------------------------------
        ("run_wall_time"),
        ("wall_time_efficiency"),
        ("throughput", {"show_if": "is_pivot"}),
        ("efficiency", {"show_if": "is_pivot"}),
        ("solver_efficiency_run"),
        ("solver_efficiency", "median", {"show_if": "is_pivot"}),
        ("solver_efficiency", "p10", {"show_if": "is_pivot"}),
        ("solver_efficiency", "p90", {"show_if": "is_pivot"}),
    ],
    description="Execution audit including outcomes, completeness, and performance.",
)


register_group(
    "audit_trial",
    [
        # Outcome
        "status",
        "failure_category",
        "failure_detail",
        # Timing
        "elapsed_seconds",
        # lifecycle timing (very useful)
        "started_at",
        "finished_at",
        # Config
        "worker_timeout",
    ],
    description="Per-trial audit details including timing and failure diagnostics.",
)

# =========================================================
# DECISION GUIDANCE
# =========================================================

register_group(
    "decision_guidance",
    [
        "overall_risk",
        "risk_signals",
        "risk_interpretation",
        ("essential_spending_risk", {}),
        ("lifestyle_spending_risk", {}),
        ("depleted", "ratio"),
    ],
    description=(
        "High-level guidance combining risk classification, signals, and key outcomes "
        "to support retirement planning decisions."
    ),
    default_opts={"show_if": "is_pivot"},
)
