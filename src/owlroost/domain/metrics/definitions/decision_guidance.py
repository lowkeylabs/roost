# domain/metrics/definitions/decision_guidance.py

from ...formatting import format_value
from ..metric_definitions import wrap_value_fn
from ..metric_registry import register_metric
from ..metric_spec import MetricSpec
from .rates import _classify_rate_regime

# =========================================================
# HELPERS
# =========================================================


def _percent_display(v, *_):
    return format_value(v, "percent") if isinstance(v, (int, float)) else (v or "-")


def _label_display(v, *_):
    if not v:
        return "-"
    return str(v).replace("_", " ").title()


def _trial_rows(r):
    return (r.get("_ctx") or {}).get("trial_rows") or []


def _filter_trials_by_regime(r, regime):
    return [t for t in _trial_rows(r) if _classify_rate_regime(t) == regime]


def _median_ss_age(trials):
    vals = [t.get("ss_age_p1") for t in trials if isinstance(t.get("ss_age_p1"), (int, float))]
    if not vals:
        return None

    vals.sort()
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def _median(values):
    if not values:
        return None

    values = sorted(values)
    n = len(values)
    mid = n // 2
    return values[mid] if n % 2 else (values[mid - 1] + values[mid]) / 2


# =========================================================
# SS PRESSURE (RATE-DRIVEN DECISION SIGNAL)
# =========================================================


def _ss_pressure(r):
    rates = r.get("rates", {})
    early = rates.get("early", {})
    infl = rates.get("inflation", {})

    early_real = early.get("real_cagr")
    inflation = infl.get("mean")

    if early_real is None or inflation is None:
        return None

    # Core intuition:
    # - bad early returns → delay SS
    # - high inflation → delay SS
    pressure = (-early_real) + inflation

    # normalize to 0–1 band (soft clamp)
    return max(0.0, min(1.0, pressure))


register_metric(
    MetricSpec(
        key="ss_pressure",
        label="SS\nPressure",
        dtype=float,
        fmt="percent",
        aggregates=["median", "p10", "p90"],
        compute_fn=_ss_pressure,
        description=(
            "Pressure to delay Social Security based on early real returns and inflation. "
            "Higher values indicate stronger incentive to delay claiming."
        ),
        display_row_fn=_percent_display,
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "High pressure to delay SS"
                if v > 0.6
                else "Moderate pressure to delay SS"
                if v > 0.3
                else "Low pressure (earlier SS viable)"
            )
        ),
    )
)


# =========================================================
# EARLY DAMAGE INDEX (SEQUENCE SEVERITY)
# =========================================================


def _early_damage(r):
    rates = r.get("rates", {})
    early = rates.get("early", {})

    cagr = early.get("real_cagr")
    worst = early.get("min_year")

    if cagr is None or worst is None:
        return None

    damage = (-cagr) + abs(worst)

    return max(0.0, min(1.0, damage))


register_metric(
    MetricSpec(
        key="early_damage_index",
        label="Early\nDamage",
        dtype=float,
        fmt="percent",
        aggregates=["median", "p10", "p90"],
        compute_fn=_early_damage,
        description=(
            "Severity of early sequence-of-returns damage combining early CAGR and worst year. "
            "Higher values indicate more stressful early market conditions."
        ),
        display_row_fn=_percent_display,
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "Severe early damage"
                if v > 0.6
                else "Moderate early stress"
                if v > 0.3
                else "Benign early sequence"
            )
        ),
    )
)


# =========================================================
# SS DECISION SENSITIVITY (STABILITY OF DECISION)
# =========================================================


def _ss_spread(r):
    try:
        ages = r.get("social_security", {}).get("ages")
        if not ages or len(ages) < 2:
            return None

        # handled at aggregate level, not trial level
        return None
    except Exception:
        return None


register_metric(
    MetricSpec(
        key="ss_sensitivity",
        label="SS\nSensitivity",
        dtype=float,
        fmt="float1",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _compute_ss_sensitivity(r),
        description=(
            "Spread between p10 and p90 Social Security claiming ages. "
            "Measures how sensitive the decision is to rate scenarios."
        ),
        display_row_fn=lambda v, *_: f"{v:.1f}y" if isinstance(v, (int, float)) else "-",
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "Highly rate-sensitive decision"
                if v and v > 5
                else "Moderately sensitive"
                if v and v > 2
                else "Stable decision"
            )
        ),
    )
)


def _compute_ss_sensitivity(r):
    try:
        p10 = r.get("ss_age_p1_p10")
        p90 = r.get("ss_age_p1_p90")

        if p10 is None or p90 is None:
            return None

        return float(p90 - p10)
    except Exception:
        return None


# =========================================================
# DECISION EXPLANATION (HIGH-LEVEL SUMMARY)
# =========================================================


def _decision_explanation(r):
    dominant = r.get("dominant_rate_regime")
    stag_pct = r.get("regime_stagflation_pct") or 0
    gold_pct = r.get("regime_goldilocks_pct") or 0
    pressure = _ss_pressure(r)

    if dominant == "stagflation" or stag_pct > 0.4:
        return "Delay SS: high exposure to stagflation risk"

    if dominant == "goldilocks" or gold_pct > 0.4:
        return "Earlier SS viable: favorable return environment"

    if pressure and pressure > 0.6:
        return "Moderate-to-strong case to delay SS"

    if pressure and pressure < 0.3:
        return "SS timing flexible; early claiming viable"

    return "Mixed rate environment; SS timing moderately sensitive"


register_metric(
    MetricSpec(
        key="decision_explanation",
        label="Decision Insight",
        dtype=str,
        aggregates=[],
        compute_fn=_decision_explanation,
        description=(
            "Plain-language explanation of Social Security decision drivers "
            "based on rate environment and early sequence conditions."
        ),
        display_row_fn=lambda v, *_: v or "-",
    )
)


def _ss_age_by_regime(r, regime):
    trials = _filter_trials_by_regime(r, regime)
    return _median_ss_age(trials)


def _spending_by_regime(r, regime):
    trials = _filter_trials_by_regime(r, regime)

    vals = [
        t.get("spending_now") for t in trials if isinstance(t.get("spending_now"), (int, float))
    ]

    return _median(vals)


register_metric(
    MetricSpec(
        key="ss_age_stagflation",
        label="SS Age\n(Stagflation)",
        dtype=float,
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _ss_age_by_regime(r, "stagflation"),
        description="Median SS claiming age in stagflation scenarios.",
        display_row_fn=lambda v, *_: f"{v:.0f}" if v else "-",
    )
)

register_metric(
    MetricSpec(
        key="ss_age_goldilocks",
        label="SS Age\n(Goldilocks)",
        dtype=float,
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _ss_age_by_regime(r, "goldilocks"),
        description="Median SS claiming age in favorable environments.",
        display_row_fn=lambda v, *_: f"{v:.0f}" if v else "-",
    )
)

register_metric(
    MetricSpec(
        key="ss_age_deflation",
        label="SS Age\n(Deflation)",
        dtype=float,
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _ss_age_by_regime(r, "deflationary_bust"),
        description="Median SS claiming age in deflationary scenarios.",
        display_row_fn=lambda v, *_: f"{v:.0f}" if v else "-",
    )
)

# =========================================================
# REGIME-CONDITIONED SPENDING
# =========================================================

register_metric(
    MetricSpec(
        key="spending_stagflation",
        label="Spend\n(Stagflation)",
        dtype=float,
        fmt="currency0",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _spending_by_regime(r, "stagflation"),
        description="Median annual spending under stagflation scenarios.",
        display_row_fn=lambda v, *_: format_value(v, "currency0") if v else "-",
    )
)

register_metric(
    MetricSpec(
        key="spending_deflation",
        label="Spend\n(Deflation)",
        dtype=float,
        fmt="currency0",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _spending_by_regime(r, "deflationary_bust"),
        description="Median annual spending under deflationary scenarios.",
        display_row_fn=lambda v, *_: format_value(v, "currency0") if v else "-",
    )
)

register_metric(
    MetricSpec(
        key="spending_moderate",
        label="Spend\n(Moderate)",
        dtype=float,
        fmt="currency0",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _spending_by_regime(r, "moderate"),
        description="Median annual spending under moderate conditions.",
        display_row_fn=lambda v, *_: format_value(v, "currency0") if v else "-",
    )
)

register_metric(
    MetricSpec(
        key="spending_goldilocks",
        label="Spend\n(Goldilocks)",
        dtype=float,
        fmt="currency0",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _spending_by_regime(r, "goldilocks"),
        description="Median annual spending under favorable environments.",
        display_row_fn=lambda v, *_: format_value(v, "currency0") if v else "-",
    )
)

register_metric(
    MetricSpec(
        key="spending_inflation_boom",
        label="Spend\n(Inflation)",
        dtype=float,
        fmt="currency0",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _spending_by_regime(r, "inflationary_boom"),
        description="Median annual spending under high inflation growth scenarios.",
        display_row_fn=lambda v, *_: format_value(v, "currency0") if v else "-",
    )
)
