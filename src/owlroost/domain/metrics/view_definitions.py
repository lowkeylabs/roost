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
        "bequest",
        "spending",
        "risk",
    ],
)


# =========================================================
# RUN VIEWS
# =========================================================

register_view(
    "run",
    "default",
    [
        "experiment",
        "case_name",
        "run",
        ("trial", "cnt"),
        ("success", "pct"),
        ("fail", "pct"),
        ("bequest", "mean"),
        ("bequest", "median"),
        ("elapsed", "mean"),
    ],
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
)

# =========================================================
# RUN DIAGNOSTICS VIEWS
# =========================================================

register_view(
    "run",
    "diagnostics",
    [
        "run",
        ("trial", "cnt"),
        "success_pct",
        "fail_pct",
        "bequest_mean",
        "bequest_median",
        "bequest_p10",
        "bequest_p90",
        "ending_assets_mean",
        "min_cushion_mean",
        "worst_drawdown_mean",
        "elapsed_mean",
    ],
)
