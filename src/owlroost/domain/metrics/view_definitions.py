from .view_registry import register_view

# =========================================================
# TRIAL VIEWS
# =========================================================

register_view(
    "trial",
    "default",
    [
        "status",
        "elapsed",
        "spending_annual",
        "spending_total",
        "bequest",
        "risk",
        "scenario_type",
    ],
    layout="table",
    description="Core trial metrics for quick inspection of outcomes and performance",
    tags=["summary"],
)


# =========================================================
# RUN VIEWS
# =========================================================

register_view(
    "run",
    "default",
    [
        "case_name",
        "experiment",
        "run",
        ("trial", "cnt"),
        "rates_method",
        ("rates_values",{"show_if":"is_pivot"}),
        ("run_specific_overrides", {"show_if": "is_pivot"}),
        ("common_overrides", {"show_if": "is_pivot"}),
        ("has_overrides_display", {"show_if": "is_table"}),
        ("success", "pct"),
        ("spending_annual", "median"),
        ("spending_total", "median"),
        ("bequest", "median"),
        # "run_overrides_display",
    ],
    description="Summary of run-level results including success rates and median outcomes",
    tags=["summary"],
)

register_view(
    "run",
    "summary",
    [
        "case_name",
        "experiment",
        "run",
        "trial",  # raw value
        "rates_method",
        ("spending_annual", "median"),
        ("spending_total", "median"),
        ("bequest", "median"),
        ("ending_assets", "mean"),
        ("min_cushion", "mean"),
        ("worst_drawdown", "mean"),
        "has_overrides_display",
    ],
    layout="pivot",
    description="Single-run summary using raw values (non-aggregated)",
    tags=["summary"],
)


# =========================================================
# TRIAL DIAGNOSTICS VIEWS
# =========================================================

# ---------------------------------------------------------
# 1. Failure-focused view
# ---------------------------------------------------------

register_view(
    "trial",
    "failures",
    [
        "status",
        "depleted",
        "years_to_depletion",
        "min_cushion",
        "worst_drawdown",
        "terminal_ratio",
        "ending_assets",
        "bequest",
        "elapsed",
    ],
    layout="pivot",
    description="Detailed view of failed trials, highlighting depletion timing and downside metrics",
    tags=["failure", "risk", "diagnostics"],
)


# ---------------------------------------------------------
# 2. Near-failure / fragility view
# ---------------------------------------------------------

register_view(
    "trial",
    "fragility",
    [
        "status",
        "min_cushion",
        "worst_drawdown",
        "terminal_ratio",
        "ending_assets",
        "bequest",
        "risk",
        "elapsed",
    ],
    layout="pivot",
    description="Identifies fragile scenarios with low cushion, high drawdowns, or near-failure conditions",
    tags=["risk", "diagnostics"],
)


# ---------------------------------------------------------
# 3. Scenario diagnostics (what caused bad outcomes)
# ---------------------------------------------------------

register_view(
    "trial",
    "scenario",
    [
        "status",
        "severity",
        "return_avg",
        "return_worst",
        "inflation_avg",
        "min_cushion",
        "bequest",
    ],
    description="Analyzes economic conditions (returns, inflation) associated with outcomes",
    tags=["scenario", "diagnostics"],
)


# ---------------------------------------------------------
# 4. Financial outcome distribution view
# ---------------------------------------------------------

if 0:
    register_view(
        "trial",
        "outcomes",
        [
            "status",
            "bequest",
            "ending_assets",
            "spending",
            "taxes",
            "roth",
        ],
        description="Distribution of financial outcomes including wealth, spending, and tax impacts",
        tags=["distribution", "summary"],
    )

# =========================================================
# RUN DIAGNOSTICS VIEWS
# =========================================================

if 0:
    register_view(
        "run",
        "diagnostics",
        [
            "expriment",
            "run",
            ("trial", "cnt"),
            ("success", "pct"),
            ("fail", "pct"),
            ("bequest", "mean"),
            ("bequest", "median"),
            ("bequest", "p10"),
            ("bequest", "p90"),
            ("ending_assets", "mean"),
            ("min_cushion", "mean"),
            ("worst_drawdown", "mean"),
            ("elapsed", "mean"),
        ],
        description="Aggregated diagnostics across trials including success rates, distribution metrics, and averages",
        tags=["diagnostics", "distribution"],
    )

# =========================================================
# RUN SPENDING / FLEXIBILITY VIEW
# =========================================================

# =========================================================
# RUN SPENDING / FLEXIBILITY VIEW (UPDATED)
# =========================================================

register_view(
    "run",
    "spendingz",
    [
        # ----------------------------------------
        # Identity
        # ----------------------------------------
        "case_name",
        "experiment",
        "run",
        "objective",
        "rates_method",
        # ----------------------------------------
        # Outcome classification (NEW)
        # ----------------------------------------
        ("fail", "pct"),
        ("trial", "cnt"),
        ("hard_fail", "cnt_true"),  # hard fail (LP infeasible)
        ("hard_fail", "pct"),  # hard fail (LP infeasible)
        ("soft_fail", "cnt_true"),  # NEW: below minimum spending
        ("soft_fail", "pct"),  # NEW: below minimum spending
        ("total_fail", "cnt_true"),  # NEW: true failure (hard OR soft)
        ("total_fail", "pct"),  # NEW: true failure (hard OR soft)
        # ----------------------------------------
        # Spending level (lifestyle)
        # ----------------------------------------
        ("spending_annual", "median"),
        ("spending_total", "median"),
        # ----------------------------------------
        # Spending variability (downside focus)
        # ----------------------------------------
        ("spending_min", "median"),
        ("spending_min", "p10"),
        ("spending_drop_pct", "mean"),
        ("spending_drop_pct", "p90"),
        # ----------------------------------------
        # Slack / flexibility
        # ----------------------------------------
        ("observed_slack_required", "mean"),
        ("observed_slack_required", "p90"),
        ("max_feasible_slack", "mean"),
        "slack_feasible",
        # ----------------------------------------
        # Behavioral realism
        # ----------------------------------------
        ("years_below_minimum", "mean"),
        ("years_below_minimum", "p90"),
        # ----------------------------------------
        # Guardrails / risk
        # ----------------------------------------
        ("min_cushion", "mean"),
        ("worst_drawdown", "mean"),
        ("terminal_ratio", "mean"),
        # ----------------------------------------
        # Outcome
        # ----------------------------------------
        ("bequest", "median"),
        # ----------------------------------------
        # Overrides
        # ----------------------------------------
        ("run_specific_overrides", {"show_if": "is_pivot"}),
        ("common_overrides", {"show_if": "is_pivot"}),
    ],
    layout="pivot",
    description="Spending profile, flexibility requirements, and true failure evaluation (hard + soft)",
    tags=["spending", "risk", "analysis"],
)

register_view(
    "run",
    "spending",
    [
        # ----------------------------------------
        # Identity
        # ----------------------------------------
        "case_name",
        "experiment",
        "run",
        "objective",
        "rates_method",
        {"separator": "section", "show_if": "is_pivot"},
        # ----------------------------------------
        # Outcome classification
        # ----------------------------------------
        ("trial", "cnt"),
        ("hard_fail", "cnt_true"),
        ("soft_fail", "cnt_true"),
        ("total_fail", "pct"),
        {"separator": "section", "show_if": "is_pivot"},
        ("run_specific_overrides", {"show_if": "is_pivot"}),
        {"separator": "section", "show_if": "is_pivot"},
        ("spending_annual", "median"),
        ("spending_total", "median"),
        ("bequest", "median"),
        {"separator": "section", "show_if": "is_pivot"},
        # ----------------------------------------
        # 🔥 Soft-fail decomposition (PIVOT ONLY)
        # ----------------------------------------
        ("soft_fail_total_years", "mean", {"show_if": "is_pivot"}),
        ("soft_fail_total_years", "p90", {"show_if": "is_pivot"}),
        ("soft_fail_max_consec", "mean", {"show_if": "is_pivot"}),
        ("soft_fail_max_consec", "p90", {"show_if": "is_pivot"}),
        ("soft_fail_ratio", "mean", {"show_if": "is_pivot"}),
        ("soft_fail_ratio", "p10", {"show_if": "is_pivot"}),
        {"separator": "section", "show_if": "is_pivot"},
        # ----------------------------------------
        # 🔥 Trigger breakdown (PIVOT ONLY)
        # ----------------------------------------
        ("soft_fail_trigger_duration", "cnt_true", {"show_if": "is_pivot"}),
        ("soft_fail_trigger_duration", "pct", {"show_if": "is_pivot"}),
        ("soft_fail_trigger_consec", "cnt_true", {"show_if": "is_pivot"}),
        ("soft_fail_trigger_consec", "pct", {"show_if": "is_pivot"}),
        ("soft_fail_trigger_severity", "cnt_true", {"show_if": "is_pivot"}),
        ("soft_fail_trigger_severity", "pct", {"show_if": "is_pivot"}),
        {"separator": "section", "show_if": "is_pivot"},
        # ----------------------------------------
        # Spending variability
        # ----------------------------------------
        ("spending_min", "median"),
        ("spending_min", "p10"),
        ("spending_drop_pct", "mean"),
        ("spending_drop_pct", "p90"),
        {"separator": "section", "show_if": "is_pivot"},
        # ----------------------------------------
        # Slack / flexibility
        # ----------------------------------------
        ("observed_slack_required", "mean"),
        ("observed_slack_required", "p90"),
        ("max_feasible_slack", "mean"),
        "slack_feasible",
        {"separator": "section", "show_if": "is_pivot"},
        # ----------------------------------------
        # Behavioral realism
        # ----------------------------------------
        ("years_below_minimum", "mean"),
        ("years_below_minimum", "p90"),
        {"separator": "section", "show_if": "is_pivot"},
        # ----------------------------------------
        # Guardrails / risk
        # ----------------------------------------
        ("min_cushion", "mean"),
        ("worst_drawdown", "mean"),
        ("terminal_ratio", "mean"),
        # ----------------------------------------
        # Outcome
        # ----------------------------------------
        {"separator": "blank", "show_if": "is_pivot"},
        # ----------------------------------------
        # Overrides
        # ----------------------------------------
        ("common_overrides", {"show_if": "is_pivot"}),
    ],
    layout="pivot",
    description="Spending profile, flexibility requirements, and true failure evaluation (hard + soft)",
    tags=["spending", "risk", "analysis"],
)
