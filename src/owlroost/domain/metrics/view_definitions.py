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
        ("essential_spending", {"show_if": "is_pivot"}),
        ("lifestyle_spending", {"show_if": "is_pivot"}),
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
        # RATE ENVIRONMENT
        # -------------------------------------------------
        {"separator": "section", "label": "RATE ENVIRONMENT"},
        ("group", "rates_characterization"),
        {"separator": "section"},
        ("group", "rates_input"),
        {"separator": "section"},
        ("group", "rates_early"),
        {"separator": "section"},
        ("group", "rates_full"),
        {"separator": "section"},
        ("group", "rates_cross"),
        {"separator": "section"},
        ("group", "rates_regime_summary"),
        {"separator": "section"},
        ("group", "rates_regime_distribution"),
        # -------------------------------------------------
        # RISK (UPDATED STRUCTURE)
        # -------------------------------------------------
        {"separator": "section", "label": "LIFESTYLE RISK"},
        ("group", "lifestyle_spending_risk"),
        {"separator": "section", "label": "ESSENTIAL RISK"},
        ("group", "essential_spending_risk"),
        {"separator": "section", "label": "DEPLETION RISK"},
        ("group", "depletion_risk"),
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
        ("group", "run_identity"),
        {"separator": "section", "label": "AUDIT"},
        ("group", "audit"),
    ],
    description="Audit view focused on infrastructure performance, completeness, and failure diagnostics.",
    tags=["audit"],
)


# =========================================================
# RUN VIEW — DECISIONS (SS + RATES + GUIDANCE)
# =========================================================

register_view(
    "run",
    "decisions",
    [
        ("group", "run_identity"),
        {"separator": "section", "label": "SOCIAL SECURITY"},
        ("group", "social_security"),
        {"separator": "section", "label": "RATE ENVIRONMENT"},
        ("group", "rates_characterization"),
        {"separator": "section", "label": "DECISION GUIDANCE"},
        ("group", "decision_guidance"),
    ],
    description=(
        "Focused view of Social Security decisions under different rate environments. "
        "Combines decision outputs, market conditions, and interpretation signals."
    ),
    tags=["decisions", "ss", "rates"],
)
