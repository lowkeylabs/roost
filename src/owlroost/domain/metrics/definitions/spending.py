# src/owlroost/domain/metrics/definitions/spending.py

from ...formatting import format_value
from ..metric_registry import register_metric
from ..metric_spec import MetricSpec, default_series_fn
from ..utils import _bool_value, wrap_value_fn

# =========================================================
# SPENDING PROFILE
# =========================================================

register_metric(
    MetricSpec(
        key="spending_now",
        path="financial.spending_profile.year0",
        label="Spending\n(Now)",
        fmt="currency_short",
        aggregates=["median"],
        description="Spending in today's dollars at the start of retirement.",
    )
)

register_metric(
    MetricSpec(
        key="spending_early",
        path="financial.spending_profile.early_avg",
        label="Spending\n(Early)",
        fmt="currency_short",
        aggregates=["median"],
        description="Average spending over the early retirement period (first ~5 years).",
    )
)

register_metric(
    MetricSpec(
        key="spending_late",
        path="financial.spending_profile.late_avg",
        label="Spending\n(Late)",
        fmt="currency_short",
        aggregates=["median"],
        description="Average spending in later years (typically survivor phase).",
    )
)

register_metric(
    MetricSpec(
        key="spending_survivor_ratio",
        path="financial.spending_profile.survivor_ratio",
        label="Survivor\nRatio",
        fmt="percent",
        aggregates=["mean"],
        description="Ratio of late-life spending to early-life spending.",
    )
)

register_metric(
    MetricSpec(
        key="spending_final",
        path="financial.spending_profile.yearN",
        label="Final\nSpending",
        fmt="currency_short",
        aggregates=["median"],
        description="Spending in the final year of the plan.",
    )
)


# =========================================================
# SPENDING THRESHOLDS
# =========================================================

register_metric(
    MetricSpec(
        key="essential_spending",
        path="financial.spending_policy.essential_spending",
        label="Essential\nSpending",
        fmt="currency",
        dtype=float,
        is_invariant=True,
        description="Essential spending level required to meet core financial needs.",
    )
)

register_metric(
    MetricSpec(
        key="lifestyle_spending",
        path="financial.spending_policy.lifestyle_spending",
        label="Lifestyle\nSpending",
        fmt="currency",
        dtype=float,
        aggregates=["median", "p10", "p90"],
        value_series_fn=lambda values, raw, rows: (
            "Not specified (no lifestyle target)"
            if not any(v is not None for v in raw)
            else default_series_fn(MetricSpec(key="tmp", label="tmp", fmt="currency"))(
                values, raw, rows
            )
        ),
        description="Target spending level that maintains the desired lifestyle.",
    )
)


register_metric(
    MetricSpec(
        key="lifestyle_spending_input",
        label="Lifestyle\n(input)",
        dtype=float,
        is_invariant=True,
        compute_fn=lambda r: (
            r.get("_inputs", {}).get("spending_policy", {}).get("lifestyle_spending") or 0
        ),
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                print(f"[DEBUG lifestyle_input] v={v}"),
                "Not set in TOML" if v in (0, None) else format_value(v, "currency"),
            )
        ),
        description="User-defined lifestyle spending (raw input value).",
    )
)


# =========================================================
# BASELINE SPENDING BEHAVIOR
# =========================================================

register_metric(
    MetricSpec(
        key="spending_ratio_min",
        path="financial.spending_summary.min_ratio",
        label="Worst\nSpending",
        fmt="percent2",
        aggregates=["mean", "p10"],
        description="Lowest spending level achieved relative to baseline spending.",
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "Plan collapses (0% spending)"
                if v == 0
                else f"Worst-case spending falls to {format_value(v, 'percent2')} of target"
            )
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_mean",
        path="financial.spending_summary.mean_ratio",
        label="Avg\nSpending",
        fmt="percent2",
        aggregates=["mean"],
        description="Average spending level relative to baseline across all years.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Average lifestyle maintained at {format_value(v, 'percent2')}"
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_median",
        path="financial.spending_summary.median_ratio",
        label="Median\nSpending",
        fmt="percent2",
        aggregates=["mean"],
        description="Median (typical) spending relative to baseline across years.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Typical spending is {format_value(v, 'percent2')} of baseline"
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_p10",
        path="financial.spending_summary.p10_ratio",
        label="P10\nSpending",
        fmt="percent2",
        aggregates=["mean"],
        description="10th percentile spending level, representing downside risk.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Downside (P10) spending is {format_value(v, 'percent2')} of target"
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_shortfall",
        path="financial.spending_summary.shortfall",
        label="Shortfall",
        fmt="percent2",
        aggregates=["mean", "p90"],
        description="Maximum reduction required from baseline spending.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Requires {format_value(v, 'percent2')} spending reduction"
        ),
    )
)

register_metric(
    MetricSpec(
        key="required_slack",
        path="financial.spending_summary.required_slack",
        label="Required\nSlack",
        fmt="percent2",
        aggregates=["mean", "p90"],
        description="Minimum spending flexibility required to sustain the plan.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Requires {format_value(v, 'percent2')} flexibility"
        ),
    )
)

register_metric(
    MetricSpec(
        key="years_under_target",
        path="financial.spending_summary.years_under_target",
        label="Years\n< Target",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Number of years in which spending falls below baseline target.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years below target spending"),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_std",
        path="financial.spending_summary.std_ratio",
        label="Spending\nVolatility",
        fmt="float2",
        aggregates=["mean"],
        description="Volatility of spending relative to baseline across the plan horizon.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Spending volatility of {format_value(v, 'float2')}"
        ),
    )
)


# =========================================================
# ESSENTIAL SPENDING (FLOOR SAFETY)
# =========================================================

register_metric(
    MetricSpec(
        key="spending_ratio_to_essential_min",
        path="financial.spending_summary.min_ratio_to_essential",
        label="Worst Year/\nEssential",
        fmt="percent2",
        aggregates=["mean", "p10"],
        description="Lowest spending relative to essential spending.",
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "Falls below essential spending"
                if v < 1
                else f"Always above essential (min {format_value(v, 'percent2')})"
            )
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_essential_mean",
        path="financial.spending_summary.mean_ratio_to_essential",
        label="Avg Year/\nEssential",
        fmt="percent2",
        aggregates=["mean"],
        description="Average spending relative to essential spending.",
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_essential_median",
        path="financial.spending_summary.median_ratio_to_essential",
        label="Median Year/\nEssential",
        fmt="percent2",
        aggregates=["mean"],
        description="Median spending relative to essential spending.",
    )
)

register_metric(
    MetricSpec(
        key="years_below_essential",
        path="financial.spending_summary.years_below_essential",
        label="Years\n< Essential",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Number of years spending falls below essential spending.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years below essential spending"),
    )
)

register_metric(
    MetricSpec(
        key="consecutive_years_below_essential",
        path="financial.spending_summary.consecutive_years_below_essential",
        label="Consec <\nEssential",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Maximum consecutive years below essential spending.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"{int(v)} consecutive years below essential spending"
        ),
    )
)

register_metric(
    MetricSpec(
        key="essential_spending_breach",
        path="financial.spending_summary.essential_spending_breach",
        label="Below\nEssential",
        dtype=int,
        fmt="count_ratio",
        aggregates=[("ratio", "count_ratio")],
        description="Trials where spending falls below essential spending.",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Essential breached", "Never breached")
        ),
    )
)


# =========================================================
# LIFESTYLE SPENDING (TARGET)
# =========================================================

register_metric(
    MetricSpec(
        key="spending_ratio_to_lifestyle_min",
        path="financial.spending_summary.min_ratio_to_lifestyle",
        label="Worst Year/\nLifestyle",
        fmt="percent2",
        aggregates=["mean", "p10"],
        description="Lowest spending relative to lifestyle target.",
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "Below lifestyle target"
                if v < 1
                else f"Maintains lifestyle (min {format_value(v, 'percent2')})"
            )
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_lifestyle_mean",
        path="financial.spending_summary.mean_ratio_to_lifestyle",
        label="Avg Year/\nLifestyle",
        fmt="percent2",
        aggregates=["mean"],
        description="Average spending relative to lifestyle target.",
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_lifestyle_median",
        path="financial.spending_summary.median_ratio_to_lifestyle",
        label="Median Year/\nLifestyle",
        fmt="percent2",
        aggregates=["mean"],
        description="Median spending relative to lifestyle target.",
    )
)

register_metric(
    MetricSpec(
        key="years_below_lifestyle",
        path="financial.spending_summary.years_below_lifestyle",
        label="Years <\nLifestyle",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Years spending falls below lifestyle target.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years below lifestyle"),
    )
)

register_metric(
    MetricSpec(
        key="consecutive_years_below_lifestyle",
        path="financial.spending_summary.consecutive_years_below_lifestyle",
        label="Consec <\nLifestyle",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Maximum consecutive years below lifestyle target.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} consecutive years below lifestyle"),
    )
)

register_metric(
    MetricSpec(
        key="lifestyle_stress_flag",
        path="financial.spending_summary.lifestyle_stress_flag",
        label="Below\nLifestyle",
        dtype=int,
        fmt="count_ratio",
        aggregates=[("ratio", "count_ratio")],
        description="Trials where spending falls below lifestyle target.",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Stress triggered", "No stress")
        ),
    )
)


# =========================================================
# WORST ABSOLUTE SPENDING
# =========================================================


def _compute_spending_worst(r):
    series = (
        r.get("financial", {})
        .get("timeseries", {})
        .get("spending", {})
        .get("actual", {})
        .get("today_by_year", [])
    )

    if not series:
        return None

    clean = [v for v in series if v is not None]
    if not clean:
        return None

    return min(clean)


register_metric(
    MetricSpec(
        key="spending_worst",
        label="Worst\nSpending",
        fmt="currency",
        aggregates=["mean", "median", "p90"],
        compute_fn=_compute_spending_worst,
        description="Lowest annual spending observed across the plan horizon.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Worst spending falls to {format_value(v, 'currency')}"
        ),
    )
)


# =========================================================
# DERIVED RELATIONSHIP
# =========================================================

register_metric(
    MetricSpec(
        key="years_between_essential_and_lifestyle",
        path="financial.spending_summary.years_between_min_and_target",
        label="Years\nAdaptive",
        fmt="int",
        aggregates=["mean"],
        description="Years where spending is below lifestyle but above essential (adaptive zone).",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years in adaptive zone"),
    )
)
