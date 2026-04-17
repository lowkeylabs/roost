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
        ("group", "overrides"),
        # -------------------------------------------------
        # PROFILE / SETUP
        # -------------------------------------------------
        {"separator": "section", "label": "PROFILE"},
        ("group", "goal"),
        {"separator": "section", "label": "STRUCTURE"},
        ("group", "run_structure"),
        # -------------------------------------------------
        # OUTCOMES
        # -------------------------------------------------
        {"separator": "section", "label": "OUTCOMES"},
        ("group", "core_outcomes_run"),
        {"separator": "section", "label": "SPENDING PROFILE"},
        ("group", "spending_profile"),
        {"separator": "section", "label": "SOCIAL SECURITY"},
        ("group", "social_security"),
        # -------------------------------------------------
        # RISK (NEW CLEAN STRUCTURE)
        # -------------------------------------------------
        {"separator": "section", "label": "LIFESTYLE RISK"},
        ("group", "lifestyle_risk"),
        {"separator": "section", "label": "SURVIVAL RISK"},
        ("group", "survival_risk"),
        {"separator": "section", "label": "RISK SUMMARY"},
        ("group", "risk_summary"),
    ],
    description="Decision-oriented run comparison using risk decomposition and outcomes",
)


# =========================================================
# RUN VIEW — AUDIT
# =========================================================

register_view(
    "run",
    "audit",
    [
        # -------------------------------------------------
        # IDENTITY
        # -------------------------------------------------
        ("group", "run_identity"),
        #        ("group", "overrides"),
        # -------------------------------------------------
        # PROFILE / SETUP
        # -------------------------------------------------
        #        {"separator": "section", "label": "PROFILE"},
        #        ("group", "goal"),
        #        {"separator": "section", "label": "STRUCTURE"},
        #        ("group", "run_structure"),
        # -------------------------------------------------
        # AUDIT
        # -------------------------------------------------
        {"separator": "section", "label": "AUDIT"},
        ("group", "audit"),
        # -------------------------------------------------
        # OPTIONAL CONTEXT (light outcomes for reference)
        # -------------------------------------------------
        #        {"separator": "section", "label": "OUTCOMES (REFERENCE)"},
        #        ("group", "core_outcomes_run"),
    ],
    description="Audit view focused on infrastructure performance, completeness, and failure diagnostics.",
    tags=["audit"],
)
