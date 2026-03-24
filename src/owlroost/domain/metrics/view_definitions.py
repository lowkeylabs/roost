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
        ("run_specific_overrides", {"show_if": "is_pivot"}),
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
