# domain/metrics/definitions/rates.py

from statistics import median

from ..metric_registry import register_metric
from ..metric_spec import MetricSpec

# =========================================================
# DISPLAY HELPERS
# =========================================================


def _percent_display(v, *_):
    from ..formatting import format_value

    return format_value(v, "percent") if isinstance(v, (int, float)) else (v or "-")


def _regime_display(v, *_):
    if not v:
        return "-"
    return v.replace("_", " ").title()


def _classify_rate_regime(t):
    real = t.get("early_real_cagr")
    infl = t.get("inflation_avg")

    if not isinstance(real, (int, float)) or not isinstance(infl, (int, float)):
        return None

    LOW_REAL = 0.01
    HIGH_REAL = 0.05
    LOW_INFL = 0.02
    HIGH_INFL = 0.04

    if real < LOW_REAL and infl > HIGH_INFL:
        return "stagflation"

    if real < LOW_REAL and infl <= LOW_INFL:
        return "deflationary_bust"

    if real >= HIGH_REAL and infl <= LOW_INFL:
        return "goldilocks"

    if real >= HIGH_REAL and infl > HIGH_INFL:
        return "inflationary_boom"

    return "moderate"


def _count_regime(r, target):
    trials = (r.get("_ctx") or {}).get("trial_rows") or []

    return sum(1 for t in trials if isinstance(t, dict) and _classify_rate_regime(t) == target)


# =========================================================
# FULL HORIZON — REAL RETURNS
# =========================================================

register_metric(
    MetricSpec(
        key="real_return",
        label="Real Return",
        path="rates.real.mean",
        fmt="percent",
        aggregates=["median", "p10", "p90"],
        description="Average real return over the full horizon.",
        display_row_fn=_percent_display,
    )
)

register_metric(
    MetricSpec(
        key="real_return_std",
        label="Volatility",
        path="rates.real.std",
        fmt="percent",
        aggregates=["median", "p10", "p90"],
        description="Volatility of real returns over the full horizon.",
        display_row_fn=_percent_display,
    )
)

register_metric(
    MetricSpec(
        key="inflation_avg",
        label="Inflation",
        path="rates.inflation.mean",
        fmt="percent",
        aggregates=["median", "p10", "p90"],
        description="Average inflation over the full horizon.",
        display_row_fn=_percent_display,
    )
)

register_metric(
    MetricSpec(
        key="stock_return",
        label="Stock Return",
        path="rates.returns.mean",
        fmt="percent",
        aggregates=["median", "p10", "p90"],
        description="Nominal stock return (S&P proxy).",
        display_row_fn=_percent_display,
    )
)

register_metric(
    MetricSpec(
        key="bond_return",
        label="Bond Return",
        path="rates.bonds.mean",
        fmt="percent",
        aggregates=["median", "p10", "p90"],
        description="Nominal bond return.",
        display_row_fn=_percent_display,
    )
)


# =========================================================
# EARLY REGIME — CORE DECISION DRIVERS
# =========================================================

register_metric(
    MetricSpec(
        key="early_real_cagr",
        label="Early Real\nCAGR",
        path="rates.early.real_cagr",
        fmt="percent",
        aggregates=["median", "p10", "p90"],
        description="Geometric real return over the early sequence window (~7 years).",
        display_row_fn=_percent_display,
    )
)

register_metric(
    MetricSpec(
        key="early_real_mean",
        label="Early Real\nMean",
        path="rates.early.real_mean",
        fmt="percent",
        aggregates=["median", "p10", "p90"],
        description="Average real return in the early sequence window.",
        display_row_fn=_percent_display,
    )
)

register_metric(
    MetricSpec(
        key="early_min_year",
        label="Worst Early\nYear",
        path="rates.early.min_year",
        fmt="percent",
        aggregates=["median", "p10", "p90"],
        description="Worst single-year real return in the early sequence window.",
        display_row_fn=_percent_display,
    )
)

# =========================================================
# EARLY REGIME — CATEGORICAL
# =========================================================

# =========================================================
# REGIME ANALYSIS
# =========================================================

register_metric(
    MetricSpec(
        key="rate_regime",
        label="Rate Regime",
        compute_fn=_classify_rate_regime,
        compute_level="trial",
        dtype=str,
        aggregates=[],
        description=(
            "Categorization of the early return environment based on real CAGR "
            "and inflation. Used to segment trials into economic regimes "
            "(stagflation, deflationary bust, moderate, goldilocks, inflationary boom)."
        ),
        display_row_fn=_regime_display,
    )
)

register_metric(
    MetricSpec(
        key="regime_stagflation_cnt",
        label="Stagflation",
        dtype=int,
        compute_level="run",
        fmt="int",
        aggregates=[],
        compute_fn=lambda r: _count_regime(r, "stagflation"),
        description=(
            "Number of trials with low real returns and high inflation, "
            "representing a stagflation environment."
        ),
    )
)

register_metric(
    MetricSpec(
        key="regime_deflation_cnt",
        label="Deflationary Bust",
        dtype=int,
        fmt="int",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _count_regime(r, "deflationary_bust"),
        description=(
            "Number of trials with low real returns and low inflation, "
            "representing a deflationary or recessionary environment."
        ),
    )
)

register_metric(
    MetricSpec(
        key="regime_moderate_cnt",
        label="Moderate",
        dtype=int,
        fmt="int",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _count_regime(r, "moderate"),
        description=(
            "Number of trials with moderate real returns and inflation, "
            "representing a neutral economic environment."
        ),
    )
)

register_metric(
    MetricSpec(
        key="regime_goldilocks_cnt",
        label="Goldilocks",
        dtype=int,
        fmt="int",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _count_regime(r, "goldilocks"),
        description=(
            "Number of trials with strong real returns and low inflation, "
            "representing a favorable economic environment."
        ),
    )
)

register_metric(
    MetricSpec(
        key="regime_inflation_boom_cnt",
        label="Inflationary Boom",
        dtype=int,
        fmt="int",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _count_regime(r, "inflationary_boom"),
        description=(
            "Number of trials with strong real returns and high inflation, "
            "representing nominal growth with inflation pressure."
        ),
    )
)


def _dominant_regime(r):
    trials = (r.get("_ctx") or {}).get("trial_rows") or []

    counts = {}
    for t in trials:
        regime = _classify_rate_regime(t)
        if regime:
            counts[regime] = counts.get(regime, 0) + 1

    if not counts:
        return None

    total = sum(counts.values())

    # compute percentages
    pct = {k: v / total for k, v in counts.items()}

    best_regime = max(pct, key=pct.get)
    best_pct = pct[best_regime]

    # -------------------------------------------------
    # NEW LOGIC
    # -------------------------------------------------

    bad_tail = pct.get("stagflation", 0) + pct.get("deflationary_bust", 0)

    # strong dominance
    if best_pct >= 0.7:
        return best_regime

    # fragile due to bad tail
    if bad_tail >= 0.25:
        return "fragile"

    # moderate dominance
    if best_pct >= 0.5:
        return f"{best_regime}*"

    # otherwise mixed
    return "mixed"


def _dominant_regime_explain(v, r):
    trials = (r.get("_ctx") or {}).get("trial_rows") or []

    counts = {}
    for t in trials:
        regime = _classify_rate_regime(t)
        if regime:
            counts[regime] = counts.get(regime, 0) + 1

    if not counts:
        return "-"

    total = sum(counts.values())
    pct = {k: v / total for k, v in counts.items()}

    # sort by prevalence
    top = sorted(pct.items(), key=lambda x: x[1], reverse=True)

    # build compact explanation
    parts = []
    for k, p in top[:2]:  # top 2 regimes
        parts.append(f"{k[:4].title()} {p:.0%}")

    # add tail signal
    bad_tail = pct.get("stagflation", 0) + pct.get("deflationary_bust", 0)
    if bad_tail >= 0.2:
        parts.append(f"Bad {bad_tail:.0%}")

    return " | ".join(parts)


register_metric(
    MetricSpec(
        key="dominant_rate_regime",
        label="Dominant\nRegime",
        dtype=str,
        compute_level="run",
        aggregates=[],
        align="center",
        compute_fn=_dominant_regime,
        description=(
            "Summary classification of the distribution of rate regimes across trials. "
            "Labels reflect both dominance and tail risk:\n"
            "- Dominant: ≥70% share\n"
            "- *: 50–70% share\n"
            "- Fragile: ≥25% adverse regimes\n"
            "- Mixed: no dominant regime"
        ),
        display_row_fn=_regime_display,
        value_series_fn=_dominant_regime_explain,
    )
)


def _pct_regime(r, target):
    trials = (r.get("_ctx") or {}).get("trial_rows") or []

    valid = [t for t in trials if _classify_rate_regime(t) is not None]
    total = len(valid)

    if not total:
        return None

    count = sum(1 for t in valid if _classify_rate_regime(t) == target)
    return count / total


register_metric(
    MetricSpec(
        key="regime_stagflation_pct",
        label="Stagflation %",
        dtype=float,
        fmt="percent",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _pct_regime(r, "stagflation"),
        description=(
            "Percentage of trials classified as stagflation (low real returns, high inflation)."
        ),
    )
)

register_metric(
    MetricSpec(
        key="regime_deflation_pct",
        label="Deflationary Bust %",
        dtype=float,
        fmt="percent",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _pct_regime(r, "deflationary_bust"),
        description=(
            "Percentage of trials classified as deflationary bust (low real returns, low inflation)."
        ),
    )
)

register_metric(
    MetricSpec(
        key="regime_moderate_pct",
        label="Moderate %",
        dtype=float,
        fmt="percent",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _pct_regime(r, "moderate"),
        description=(
            "Percentage of trials classified as moderate regime (mid-range real returns and inflation)."
        ),
    )
)

register_metric(
    MetricSpec(
        key="regime_goldilocks_pct",
        label="Goldilocks %",
        dtype=float,
        fmt="percent",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _pct_regime(r, "goldilocks"),
        description=(
            "Percentage of trials classified as goldilocks (strong real returns, low inflation)."
        ),
    )
)

register_metric(
    MetricSpec(
        key="regime_inflation_boom_pct",
        label="Inflationary Boom %",
        dtype=float,
        fmt="percent",
        compute_level="run",
        aggregates=[],
        compute_fn=lambda r: _pct_regime(r, "inflationary_boom"),
        description=(
            "Percentage of trials classified as inflationary boom (strong real returns, high inflation)."
        ),
    )
)


# =========================================================
# EARLY VS FULL CONTRAST (ADVANCED SIGNAL)
# =========================================================


def _early_vs_full_gap_trial(t):
    early = t.get("early_real_mean")
    full = t.get("real_return")

    if not isinstance(early, (int, float)):
        return None
    if not isinstance(full, (int, float)):
        return None

    return early - full


def _early_vs_full_gap(r):
    vals = []

    for t in (r.get("_ctx") or {}).get("trial_rows") or []:
        early = t.get("early_real_mean")
        full = t.get("real_return")

        if isinstance(early, (int, float)) and isinstance(full, (int, float)):
            vals.append(early - full)

    return median(vals) if vals else None


register_metric(
    MetricSpec(
        key="early_vs_full_real_gap",
        label="Early vs Full\nGap",
        dtype=float,
        fmt="percent",
        compute_level="trial",  # 🔥 CRITICAL CHANGE
        compute_fn=_early_vs_full_gap_trial,
        aggregates=["median", "p10", "p90"],
        display_row_fn=_percent_display,
        description=(
            "Difference between early-period real returns and full-horizon real returns. "
            "Negative values indicate early underperformance (sequence-of-returns risk)."
        ),
    )
)
