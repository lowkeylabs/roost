# src/owlroost/domain/metrics/definitions/risk.py

# =========================================================
# RISK
# =========================================================

from ...formatting import format_value
from ..metric_registry import register_metric
from ..metric_spec import MetricSpec
from ..utils import _as_float, wrap_value_fn

# =========================================================
# CORE OUTCOME METRICS
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
# DISTRIBUTION RISK SIGNALS
# =========================================================


def _compute_distribution_risk_flags(r):
    flags = 0

    p10_ess = _as_float(r.get("spending_ratio_to_essential_min_p10"))
    p10_life = _as_float(r.get("spending_ratio_to_lifestyle_min_p10"))
    breach = _as_float(r.get("lifestyle_stress_flag_ratio"))

    if p10_ess is not None and p10_ess < 1.0:
        flags += 1

    if p10_ess is not None and p10_ess < 0.5:
        flags += 1

    if p10_life is not None and p10_life < 1.0:
        flags += 1

    if breach is not None and breach > 0.1:
        flags += 1

    return flags


def _compute_path_risk_signals(r):
    flags = r.get("risk.summary.flags")
    return flags if isinstance(flags, list) else []


def _compute_distribution_risk_signals(r):
    signals = []

    p10_ess = _as_float(r.get("spending_ratio_to_essential_min_p10"))
    p10_life = _as_float(r.get("spending_ratio_to_lifestyle_min_p10"))
    breach = _as_float(r.get("lifestyle_stress_flag_ratio"))

    years_ess = r.get("years_below_essential_mean")
    years_life = r.get("years_below_lifestyle_mean")

    # --- PRIORITY ORDER ---

    if p10_ess is not None and p10_ess < 0.5:
        return ["Severe essential shortfall risk"]

    if p10_ess is not None and p10_ess < 1.0:
        signals.append("Below essential spending in tail scenarios")

    if years_ess is not None and years_ess > 0:
        signals.append("Persistent essential shortfall")

    if years_life is not None and years_life > 0:
        signals.append("Sustained lifestyle shortfall")

    if p10_life is not None and p10_life < 1.0:
        signals.append("Lifestyle degradation risk")

    if breach is not None:
        if breach > 0.9:
            signals.append("Frequent shortfalls")
        elif breach > 0.1:
            signals.append("Occasional shortfalls")

    return signals[:3]


def _compute_risk_signals_run(r):
    trial_count = r.get("trial") or r.get("trial_cnt") or r.get("trial_count") or 1

    if trial_count == 1:
        signals = _compute_path_risk_signals(r)
    else:
        signals = _compute_distribution_risk_signals(r)

    return signals if signals else None


def _compute_risk_flags_run(r):
    signals = _compute_risk_signals_run(r)
    return len(signals) if signals else 0


def _compute_risk_interpretation(r):
    signals = r.get("risk_signals") or []

    if not signals:
        return None

    primary = signals[0]

    mapping = {
        "Severe essential shortfall risk": "Plan fails to meet essential spending in worst-case scenarios.",
        "Below essential spending in tail scenarios": "Essential spending is not sustained in adverse scenarios.",
        "Persistent essential shortfall": "Essential spending is not maintained over extended periods.",
        "Sustained lifestyle shortfall": "Lifestyle spending is not consistently maintained.",
        "Lifestyle degradation risk": "Spending occasionally falls below lifestyle targets.",
        "Frequent shortfalls": "Shortfalls occur across most scenarios.",
        "Occasional shortfalls": "Shortfalls occur in a minority of scenarios.",
    }

    return mapping.get(primary, "Mixed risk signals present.")


# =========================================================
# RISK LEVEL CLASSIFICATION
# =========================================================


def _lifestyle_level(r):
    p10 = _as_float(r.get("spending_ratio_to_lifestyle_min_p10"))
    years = r.get("years_below_lifestyle_mean")

    if p10 is not None:
        if p10 < 0.5:
            return "high"
        if p10 < 1.0:
            return "moderate"

    if years is not None and years > 0:
        return "moderate"

    return "low"


def _essential_level(r):
    p10 = _as_float(r.get("spending_ratio_to_essential_min_p10"))
    years = r.get("years_below_essential_mean")

    if p10 is not None:
        if p10 < 0.5:
            return "high"
        if p10 < 1.0:
            return "moderate"

    if years is not None and years > 0:
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
# REGISTER METRICS
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
