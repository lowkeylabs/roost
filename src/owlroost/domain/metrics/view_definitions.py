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
        {"separator": "section", "label": "OUTCOMES"},
        ("group", "core_outcomes_trial"),
        {"separator": "section", "label": "SPENDING"},
        ("minimum_spending", {"show_if": "is_pivot"}),
        ("acceptable_spending", {"show_if": "is_pivot"}),
        ("group", "trial_spending_detail"),
        {"separator": "section", "label": "RISK"},
        ("group", "portfolio_risk_trial"),
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
        # -------------------------------------------------
        # IDENTITY
        # -------------------------------------------------
        ("group", "run_identity"),
        # -------------------------------------------------
        # PROFILE / SETUP
        # -------------------------------------------------
        {"separator": "section", "label": "PROFILE"},
        ("group", "overrides"),
        ("group", "run_structure"),
        # -------------------------------------------------
        # OUTCOMES (what do I get?)
        # -------------------------------------------------
        {"separator": "section", "label": "OUTCOMES"},
        ("group", "outcomes"),
        # SPENDING PROFILE
        {"separator": "section", "label": "SPENDING PROFILE"},
        ("group", "spending_profile"),
        # -------------------------------------------------
        # LIFESTYLE (comfort)
        # -------------------------------------------------
        {"separator": "section", "label": "LIFESTYLE"},
        ("group", "lifestyle"),
        # -------------------------------------------------
        # SAFETY (hard constraint)
        # -------------------------------------------------
        {"separator": "section", "label": "SAFETY"},
        ("group", "safety"),
    ],
    description="Decision-oriented run comparison: outcomes, lifestyle, and safety",
)

register_view(
    "run",
    "default6",
    [
        # Identity
        ("group", "run_identity"),
        {"separator": "section", "label": "RISK"},
        ("group", "overrides"),
        {"separator": "section", "label": "RISK"},
        ("group", "core_outcomes_run"),
        {"separator": "section", "label": "RISK"},
        ("group", "acceptable_lifestyle"),
        {"separator": "section", "label": "RISK"},
        ("group", "minimum_safety"),
        # Overall evaluation (REPLACES Bad/Review)
        # "run_status_summary",
        # Feasibility
        # ("solver_fail", "pct"),
        # Risk FIRST (most important)
        # ("spending_ratio_min", "mean"),
        # Then lifestyle
        # ("spending_annual", "median"),
        # Then upside (pivot only)
        # ("bequest", "median", {"show_if": "is_pivot"}),
    ],
    description="Compact run dashboard prioritizing downside risk and decision clarity",
)

register_view(
    "run",
    "default4",
    [
        # -------------------------------------------------
        # IDENTITY
        # -------------------------------------------------
        "case_name",
        "experiment",
        "run",
        ("trial", "cnt"),
        # -------------------------------------------------
        # CORE DASHBOARD (TABLE + PIVOT)
        # -------------------------------------------------
        {"separator": "section", "label": "SUMMARY"},
        ("group", "run_dashboard_core"),
        # -------------------------------------------------
        # OUTCOMES (PIVOT ONLY)
        # -------------------------------------------------
        {"separator": "section", "label": "OUTCOMES", "show_if": "is_pivot"},
        ("group", "run_outcomes_pivot", {"show_if": "is_pivot"}),
        # -------------------------------------------------
        # RISK / EDGE (PIVOT ONLY)
        # -------------------------------------------------
        {"separator": "section", "label": "RISK", "show_if": "is_pivot"},
        ("group", "run_risk_pivot", {"show_if": "is_pivot"}),
        # -------------------------------------------------
        # DETAILED PROFILE FLAGS (PIVOT ONLY)
        # -------------------------------------------------
        {"separator": "section", "label": "PROFILE DETAIL", "show_if": "is_pivot"},
        ("group", "run_profile_flags", {"show_if": "is_pivot"}),
    ],
    description="Adaptive run dashboard: compact triage (table) with expanded pivot analysis",
    tags=["summary", "dashboard"],
)

register_view(
    "run",
    "default3",
    [
        # -------------------------------------------------
        # IDENTITY
        # -------------------------------------------------
        ("group", "run_identity"),
        ("trial", "cnt"),
        # -------------------------------------------------
        # WHAT KIND OF RUN IS THIS?
        # -------------------------------------------------
        {"separator": "section", "label": "PROFILE"},
        ("group", "run_profile_flags"),
        # -------------------------------------------------
        # DID IT WORK?
        # -------------------------------------------------
        {"separator": "section", "label": "FEASIBILITY"},
        ("solver_fail", "pct"),
        # -------------------------------------------------
        # WHAT DID I GET?
        # -------------------------------------------------
        {"separator": "section", "label": "OUTCOME"},
        ("spending_annual", "median"),
        ("bequest", "median"),
        # -------------------------------------------------
        # SHOULD I WORRY?
        # -------------------------------------------------
        {"separator": "section", "label": "STRESS"},
        ("spending_ratio_min", "mean"),
        ("floor_breach", "pct"),
        # -------------------------------------------------
        # HOW CLOSE TO THE EDGE?
        # -------------------------------------------------
        {"separator": "section", "label": "EDGE"},
        ("min_cushion", "mean"),
    ],
    description="Run-level dashboard highlighting intent, outcomes, and risk signals for quick triage",
    tags=["summary", "dashboard"],
)

register_view(
    "run",
    "default2",
    [
        # -------------------------------------------------
        # WHAT IS THIS RUN?
        # -------------------------------------------------
        ("group", "run_identity"),
        ("group", "run_structure"),
        # -------------------------------------------------
        # WHAT DID I ASK FOR? (key knobs only)
        # -------------------------------------------------
        {"separator": "section", "label": "SETUP"},
        "rates_method",
        "objective",
        ("minimum_spending", {"show_if": "is_table"}),
        ("acceptable_spending", {"show_if": "is_table"}),
        # -------------------------------------------------
        # DID IT WORK?
        # -------------------------------------------------
        {"separator": "section", "label": "FEASIBILITY"},
        ("solver_fail", "pct"),
        # -------------------------------------------------
        # WHAT DID I GET?
        # -------------------------------------------------
        {"separator": "section", "label": "OUTCOME"},
        ("spending_annual", "median"),
        ("bequest", "median"),
        ("ending_assets", "median"),
        # -------------------------------------------------
        # SHOULD I WORRY?
        # -------------------------------------------------
        {"separator": "section", "label": "STRESS SIGNALS"},
        ("spending_ratio_min", "mean"),
        ("years_below_acceptable", "mean"),
        ("floor_breach", "pct"),
        # -------------------------------------------------
        # PORTFOLIO RISK (1–2 signals only)
        # -------------------------------------------------
        {"separator": "section", "label": "PORTFOLIO"},
        ("min_cushion", "mean"),
        ("terminal_ratio", "mean"),
    ],
    description="High-level comparison of runs highlighting feasibility, outcomes, and stress signals",
    tags=["summary"],
)

register_view(
    "run",
    "default1",
    [
        # Identity + structure
        ("group", "run_identity"),
        ("group", "run_structure"),
        {"separator": "section", "label": "FEASIBILITY", "show_if": "is_pivot"},
        ("group", "feasibility"),
        {"separator": "section", "label": "OUTCOMES", "show_if": "is_pivot"},
        ("group", "core_outcomes_run"),
        {"separator": "section", "label": "TARGET", "show_if": "is_pivot"},
        ("group", "target_performance"),
        {"separator": "section", "label": "ACCEPTABLE", "show_if": "is_pivot"},
        ("group", "acceptable_lifestyle"),
        {"separator": "section", "label": "MINIMUM", "show_if": "is_pivot"},
        ("group", "minimum_safety"),
        {"separator": "section", "label": "RISK", "show_if": "is_pivot"},
        ("group", "portfolio_risk"),
        {"separator": "section", "label": "OVERRIDES", "show_if": "is_pivot"},
        ("group", "overrides"),
    ],
    description="Run-level summary including feasibility, spending risk tiers, and portfolio sustainability",
    tags=["summary"],
)
