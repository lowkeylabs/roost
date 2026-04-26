from .view_registry import register_view

# =========================================================
# TRIAL VIEWS
# =========================================================

register_view(
    "trial",
    "default",
    [
        ("group", "run_identity_trial"),
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

register_view(
    "trial",
    "audit",
    [
        ("group", "run_identity_trial"),
        ("group", "audit_trial"),
    ],
    layout="table",
    description="Trial-level results including financial outcomes and spending stress behavior",
    tags=["summary"],
)

register_view(
    "run",
    "signatures",
    [
        ("group", "run_identity"),
        "signature",
        "run_specific_overrides",
        "common_overrides",
    ],
    layout="table",
    description="x",
    tags=["summary"],
)


# =========================================================
# RUN VIEWS
# =========================================================

register_view(
    "run",
    "default",
    [
        ("group", "run_identity"),
    ],
    description="Decision-oriented run comparison using risk decomposition and outcomes",
)


register_view(
    "run",
    "default",
    [
        # -------------------------------------------------
        # IDENTITY
        # -------------------------------------------------
        ("group", "run_identity"),
        {"separator": "section", "label": "OVERRIDES"},
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

register_view(
    "run",
    "timing",
    [
        ("group", "run_identity"),

        {"separator": "section", "label": "TIMING"},
        ("group", "timing"),
    ],
    description="Run-level timing and performance analysis.",
    tags=["timing", "performance"],
)

register_view(
    "trial",
    "timing",
    [
        ("group", "run_identity_trial"),

        {"separator": "section", "label": "TIMING"},
        "elapsed_seconds",
        "started_at",
        "finished_at",

        {"separator": "section", "label": "STATUS"},
        "status",
        "failure_category",
    ],
    layout="table",
    description="Per-trial timing and execution diagnostics.",
    tags=["timing"],
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
