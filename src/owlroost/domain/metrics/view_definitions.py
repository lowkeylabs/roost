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
        # =====================================================
        # Core financial outcome
        # =====================================================
        "bequest",
        "ending_assets",
        {"separator": "section"},
        # =====================================================
        # Spending (per-trial reality)
        # =====================================================
        "spending_ratio_min",  # worst vs target
        "spending_ratio_to_acceptable_min",
        "spending_ratio_to_minimum_min",
        "years_under_target",
        "years_below_acceptable",
        "years_below_minimum",
        "spending_stress_flag",
        {"separator": "section"},
        # =====================================================
        # Portfolio risk
        # =====================================================
        "min_cushion",
        "worst_drawdown",
        "terminal_ratio",
        "terminal_assets_to_spending",
    ],
    layout="table",
    description="Trial-level results including financial outcomes and spending stress behavior",
    tags=["summary"],
)

# =========================================================
# RUN VIEWS
# =========================================================

register_view(
    "run",
    "default",
    [
        # =====================================================
        # Identity
        # =====================================================
        "case_name",
        "experiment",
        "run",
        # =====================================================
        # Structure
        # =====================================================
        ("trial", "cnt"),
        "rates_method",
        "objective",
        {"separator": "section", "show_if": "is_pivot"},
        # =====================================================
        # Feasibility
        # =====================================================
        ("solver_fail", "cnt_true"),
        ("solver_fail", "pct", {"show_if": "is_pivot"}),
        {"separator": "section", "show_if": "is_pivot"},
        # =====================================================
        # Core Outcomes
        # =====================================================
        ("spending_annual", "median"),
        ("spending_total", "median"),
        ("bequest", "median"),
        ("bequest", "mean", {"show_if": "is_pivot"}),
        ("ending_assets", "median", {"show_if": "is_pivot"}),
        {"separator": "section", "show_if": "is_pivot"},
        # =====================================================
        # TARGET (Goal Performance)
        # =====================================================
        ("spending_ratio_min", "mean"),
        ("spending_shortfall", "mean"),
        ("years_under_target", "mean"),
        ("spending_ratio_p10", "mean", {"show_if": "is_pivot"}),
        ("spending_ratio_median", "mean", {"show_if": "is_pivot"}),
        ("spending_ratio_mean", "mean", {"show_if": "is_pivot"}),
        ("spending_ratio_std", "mean", {"show_if": "is_pivot"}),
        ("spending_shortfall", "p90", {"show_if": "is_pivot"}),
        ("years_under_target", "p90", {"show_if": "is_pivot"}),
        ("required_slack", "mean"),
        ("required_slack", "p90", {"show_if": "is_pivot"}),
        {"separator": "section", "show_if": "is_pivot"},
        # =====================================================
        # ACCEPTABLE (Lifestyle Tolerance)
        # =====================================================
        ("spending_ratio_to_acceptable_min", "mean"),
        ("years_below_acceptable", "mean"),
        ("consecutive_years_below_acceptable", "mean"),
        ("years_below_acceptable", "p90", {"show_if": "is_pivot"}),
        ("consecutive_years_below_acceptable", "p90", {"show_if": "is_pivot"}),
        ("spending_stress_flag", "cnt_true"),
        ("spending_stress_flag", "pct", {"show_if": "is_pivot"}),
        {"separator": "section", "show_if": "is_pivot"},
        # =====================================================
        # MINIMUM (Floor Safety)
        # =====================================================
        ("spending_ratio_to_minimum_min", "mean"),
        ("years_below_minimum", "mean"),
        ("years_below_minimum", "p90", {"show_if": "is_pivot"}),
        ("floor_breach", "cnt_true"),
        ("floor_breach", "pct", {"show_if": "is_pivot"}),
        {"separator": "section", "show_if": "is_pivot"},
        # =====================================================
        # Portfolio Risk (asset-based)
        # =====================================================
        ("min_cushion", "mean"),
        ("worst_drawdown", "mean"),
        ("terminal_ratio", "mean", {"show_if": "is_pivot"}),
        ("terminal_assets_to_spending", "mean", {"show_if": "is_pivot"}),
        {"separator": "section", "show_if": "is_pivot"},
        # =====================================================
        # Overrides
        # =====================================================
        ("run_specific_overrides", {"show_if": "is_pivot"}),
        ("common_overrides", {"show_if": "is_pivot"}),
    ],
    description="Run-level summary including feasibility, spending risk tiers, and portfolio sustainability",
    tags=["summary"],
)
