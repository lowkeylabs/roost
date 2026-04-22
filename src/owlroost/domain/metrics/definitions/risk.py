# src/owlroost/domain/metrics/definitions/risk.py

# =========================================================
# RISK
# =========================================================

from ...formatting import format_value
from ..metric_registry import register_metric
from ..metric_spec import MetricSpec
from ..utils import _as_float, wrap_value_fn

# =========================================================
# CORE OUTCOME METRICS (UNCHANGED)
# =========================================================

register_metric(
    MetricSpec(
        key="min_cushion",
        path="risk.outcome.cushion.min_cushion_ratio",
        label="Min Cushion",
        fmt="float2",
        aggregates=["mean"],
        description="Minimum ratio of assets to spending observed over the lifetime of the plan.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"{format_value(v, 'float2')}× spending buffer at minimum point"
        ),
    )
)

register_metric(
    MetricSpec(
        key="worst_drawdown",
        path="risk.outcome.drawdown.worst_drawdown_factor",
        label="Worst Drawdown",
        fmt="percent2",
        aggregates=["mean"],
        description="Largest peak-to-trough decline in portfolio value during the plan.",
    )
)

register_metric(
    MetricSpec(
        key="terminal_ratio",
        path="risk.outcome.terminal.spending_to_assets_ratio",
        label="Terminal S/A",
        fmt="percent2",
        aggregates=["mean"],
        description="Final ratio of spending to remaining assets at the end of the plan.",
    )
)

register_metric(
    MetricSpec(
        key="terminal_assets_to_spending",
        label="Terminal A/S",
        fmt="float2",
        aggregates=["mean"],
        compute_level="run",
        compute_fn=lambda r: (
            1 / r.get("terminal_ratio") if r.get("terminal_ratio") not in (None, 0) else None
        ),
        description="Final assets divided by final spending.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Assets cover {format_value(v, 'float2')}× final spending"
        ),
    )
)

register_metric(
    MetricSpec(
        key="outcome_risk",
        path="risk.outcome.classification.risk_level",
        label="Outcome\nRisk",
        dtype=str,
        description="Risk classification based on plan outcomes only.",
    )
)

register_metric(
    MetricSpec(
        key="scenario_severity",
        path="risk.summary.scenario_severity",
        label="Scenario\nSeverity",
        fmt="percent2",
        aggregates=["mean"],
        description="Normalized severity of the return environment.",
    )
)

register_metric(
    MetricSpec(
        key="depleted",
        path="risk.summary.depleted",
        label="Depleted",
        dtype=int,
        fmt="count_ratio",
        aggregates=[("ratio", "count_ratio")],
        description="Indicates whether assets are depleted during the plan.",
    )
)

register_metric(
    MetricSpec(
        key="risk_flag_count",
        path="risk.summary.flag_count",
        label="Risk\nFlags",
        fmt="int",
        aggregates=["mean"],
        description="Number of risk signals triggered.",
    )
)

# =========================================================
# NEW: STRUCTURED RISK MODEL
# =========================================================


def _profile_lifestyle(r):
    return {
        "p10": _as_float(r.get("spending_ratio_to_lifestyle_min_p10")),
        "years": r.get("years_below_lifestyle_mean") or 0,
        "consec": r.get("consecutive_years_below_lifestyle_mean") or 0,
        "breach": _as_float(r.get("lifestyle_stress_flag_ratio")) or 0,
    }


def _profile_essential(r):
    return {
        "p10": _as_float(r.get("spending_ratio_to_essential_min_p10")),
        "years": r.get("years_below_essential_mean") or 0,
        "consec": r.get("consecutive_years_below_essential_mean") or 0,
        "breach": _as_float(r.get("essential_spending_breach_ratio")) or 0,
    }


def _classify(p):
    p10 = p["p10"]
    years = p["years"]
    consec = p["consec"]
    breach = p["breach"]

    return {
        "severity": "severe" if (p10 is not None and p10 < 1.0) else "strong",
        "frequency": (
            "none"
            if breach == 0
            else "rare"
            if breach < 0.05
            else "occasional"
            if breach < 0.2
            else "frequent"
        ),
        "persistence": ("none" if years == 0 else "episodic" if consec <= 1 else "persistent"),
    }


# =========================================================
# SIGNALS (REWRITTEN)
# =========================================================


def _signals_from_profile(p, label):
    c = _classify(p)
    signals = []

    if c["severity"] == "severe":
        signals.append(f"{label} shortfall in adverse scenarios")

    if c["persistence"] == "persistent":
        signals.append(f"Persistent {label.lower()} shortfall")

    if c["frequency"] == "frequent":
        signals.append(f"Frequent {label.lower()} shortfalls")
    elif c["frequency"] == "occasional":
        signals.append(f"Occasional {label.lower()} shortfalls")
    elif c["frequency"] == "rare":
        signals.append(f"Rare {label.lower()} shortfalls")

    return signals


def _compute_path_risk_signals(r):
    flags = r.get("risk.summary.flags")
    return flags if isinstance(flags, list) else []


def _compute_distribution_risk_signals(r):
    life = _profile_lifestyle(r)
    ess = _profile_essential(r)

    signals = []
    signals.extend(_signals_from_profile(ess, "Essential"))
    signals.extend(_signals_from_profile(life, "Lifestyle"))

    return signals[:3] or None


def _compute_risk_signals_run(r):
    trial_count = r.get("trial") or r.get("trial_cnt") or r.get("trial_count") or 1

    if trial_count == 1:
        return _compute_path_risk_signals(r)

    return _compute_distribution_risk_signals(r)


def _compute_risk_flags_run(r):
    signals = _compute_risk_signals_run(r)
    return len(signals) if signals else 0


# =========================================================
# INTERPRETATION (REWRITTEN)
# =========================================================


def _compute_risk_interpretation(r):
    life_profile = _profile_lifestyle(r)
    ess_profile = _profile_essential(r)

    life = _classify(life_profile)
    ess = _classify(ess_profile)

    # Essential dominates
    if ess["severity"] == "severe":
        return "Plan fails to meet essential spending in adverse scenarios."

    if ess["frequency"] == "none":
        essential_msg = "Essential spending is fully protected."
    else:
        essential_msg = "Essential spending is mostly protected."

    # Lifestyle interpretation
    if life["frequency"] == "none":
        lifestyle_msg = "Lifestyle is fully maintained."

    elif life["frequency"] == "rare":
        if life_profile["consec"] > 1:
            lifestyle_msg = (
                "Lifestyle is maintained in nearly all scenarios, with rare clustered shortfalls."
            )
        else:
            lifestyle_msg = (
                "Lifestyle is maintained in nearly all scenarios with rare, isolated shortfalls."
            )

    elif life["frequency"] == "occasional":
        lifestyle_msg = "Lifestyle occasionally falls below target."

    elif life["frequency"] == "frequent":
        lifestyle_msg = "Lifestyle is frequently not maintained."

    else:
        lifestyle_msg = "Mixed lifestyle outcomes."

    return f"{essential_msg} {lifestyle_msg}"


# =========================================================
# RISK LEVELS (UPDATED)
# =========================================================


def _essential_level(r):
    c = _classify(_profile_essential(r))
    if c["severity"] == "severe":
        return "high"
    if c["frequency"] in ("occasional", "frequent"):
        return "moderate"
    return "low"


def _lifestyle_level(r):
    c = _classify(_profile_lifestyle(r))
    if c["severity"] == "severe":
        return "high"
    if c["frequency"] in ("occasional", "frequent") or c["persistence"] == "persistent":
        return "moderate"
    return "low"


def _compute_risk_summary(r):
    essential = _essential_level(r)
    lifestyle = _lifestyle_level(r)

    if essential == "high":
        return "At risk of depletion"
    if essential == "moderate":
        return "At risk"
    if lifestyle == "high":
        return "Severely constrained"
    if lifestyle == "moderate":
        return "Safe but constrained"
    return "Comfortable and safe"


# =========================================================
# REGISTER METRICS (UNCHANGED KEYS)
# =========================================================

register_metric(
    MetricSpec(
        key="risk_flags",
        label="Risk\nFlags",
        dtype=int,
        compute_fn=_compute_risk_flags_run,
        compute_level="run",
        is_invariant=True,
    )
)

register_metric(
    MetricSpec(
        key="risk_signals",
        label="Risk\nSignals",
        dtype=str,
        compute_fn=_compute_risk_signals_run,
        compute_level="run",
        is_invariant=True,
        display_row_fn=lambda v, *_: "\n".join(v) if isinstance(v, list) else "-",
        value_series_fn=lambda values, *_: (
            "\n".join(values[0]) if values and isinstance(values[0], list) else "-"
        ),
    )
)

register_metric(
    MetricSpec(
        key="risk_interpretation",
        label="Risk\nInterpretation",
        dtype=str,
        compute_fn=_compute_risk_interpretation,
        compute_level="run",
        is_invariant=True,
    )
)

register_metric(
    MetricSpec(
        key="essential_spending_risk",
        label="Essential\nSpending\nRisk",
        dtype=str,
        compute_level="run",
        compute_fn=_essential_level,
        is_invariant=True,
        description="Risk of failing to sustain essential spending.",
    )
)

register_metric(
    MetricSpec(
        key="lifestyle_spending_risk",
        label="Lifestyle\nSpending\nRisk",
        dtype=str,
        compute_level="run",
        compute_fn=_lifestyle_level,
        is_invariant=True,
        description="Risk of failing to sustain lifestyle spending.",
    )
)

register_metric(
    MetricSpec(
        key="overall_risk",
        label="Overall\nRisk",
        dtype=str,
        compute_fn=_compute_risk_summary,
        compute_level="run",
        is_invariant=True,
        description="Composite risk classification.",
    )
)
