from ..formatting import format_value
from .metric_registry import register_metric
from .metric_spec import MetricSpec

# =========================================================
# Helpers
# =========================================================

RATES_METHOD_ABBR = {
    "historical": "Hist",
    "historical average": "HAvg",
    "histogaussian": "HGauss",
    "histolognormal": "HLog",
    "bootstrap_sor": "bSor",
    "var": "VaR",
    "garch_dcc": "Gdcc",
}


def _bool_value(value: bool, true_msg: str, false_msg: str) -> str:
    return true_msg if value else false_msg


def wrap_value_fn(fn):
    def series_fn(values, raw, rows):
        clean = [v for v in values if v is not None]
        if not clean:
            return "-"
        return fn(clean[0], rows[0] if rows else None)

    return series_fn


def _as_float(v):
    if v is None:
        return None

    # already numeric
    if isinstance(v, (int, float)):
        return float(v)

    # percent string
    if isinstance(v, str):
        if v.endswith("%"):
            return float(v.strip("%")) / 100.0
        if "/" in v:
            num, den = v.split("/")
            return float(num) / float(den)

    # 🔥 CRITICAL: handle tuple (count_ratio)
    if isinstance(v, tuple) and len(v) == 2:
        num, den = v
        try:
            return float(num) / float(den) if den else None
        except Exception:
            return None

    return None


# =========================================================
# CORE OUTCOMES
# =========================================================

register_metric(
    MetricSpec(
        key="spending_annual",
        path="financial.spending.year0.today",
        label="Annual\nSpending",
        fmt="currency_short",
        aggregates=["median"],
        description="Annual spending in today's dollars at the start of retirement (year 0).",
    )
)

register_metric(
    MetricSpec(
        key="spending_total",
        path="financial.spending.total.today",
        label="Total\nSpending",
        fmt="currency_short",
        aggregates=["median"],
        description="Total lifetime spending in today's dollars across the full planning horizon.",
    )
)

register_metric(
    MetricSpec(
        key="taxes_total",
        path="financial.taxes.total.today",
        label="Total\nTaxes",
        fmt="currency_short",
        aggregates=["median"],
        description="Total lifetime taxes in today's dollars across the full planning horizon.",
    )
)


register_metric(
    MetricSpec(
        key="bequest",
        path="financial.bequest.total.today",
        label="Bequest",
        fmt="currency_short",
        aggregates=["median", "mean"],
        description="Remaining estate value at the end of the plan after all spending and taxes.",
    )
)

register_metric(
    MetricSpec(
        key="ending_assets",
        path="risk.outcome.assets.final_today",
        label="Ending Assets",
        fmt="currency_short",
        aggregates=["median"],
        description="Total assets remaining at the end of the plan in today's dollars.",
    )
)


# =========================================================
# STATUS
# =========================================================

register_metric(
    MetricSpec(
        key="status",
        path="run_status.status",
        label="Status",
        dtype=str,
        description="Outcome of the solver for this trial (solved or failed).",
        value_series_fn=wrap_value_fn(lambda v, _: "Solved" if v == "solved" else "Failed"),
    )
)

register_metric(
    MetricSpec(
        key="success",
        label="Success",
        compute_fn=lambda d: 1 if d.get("status") == "solved" else 0,
        fmt="percent",
        aggregates=["cnt", "pct"],
        description="Indicates whether the plan solved successfully (1) or failed (0).",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Successful outcome", "Unsuccessful outcome")
        ),
    )
)

register_metric(
    MetricSpec(
        key="solver_fail",
        label="Solver\nFail",
        dtype=int,
        aggregates=[("cnt_true", "int"), ("pct", "percent")],
        compute_fn=lambda r: 0 if r.get("status") == "solved" else 1,
        description="Indicator that the solver failed to produce a valid plan.",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Solver failure occurred", "No solver failure")
        ),
    )
)

register_metric(
    MetricSpec(
        key="elapsed",
        path="timing.elapsed_seconds",
        label="Elapsed",
        fmt="float2",
        aggregates=["mean"],
        description="Time taken to solve the plan in seconds.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{format_value(v, 'float2')} seconds"),
    )
)

# =========================================================
# INPUT CONTEXT
# =========================================================

register_metric(
    MetricSpec(
        key="case_name",
        label="Case name",
        dtype=str,
        align="left",
        is_invariant=True,
        description="Name of the planning case or scenario.",
    )
)

register_metric(
    MetricSpec(
        key="case",
        label="Case",
        aggregates=["cnt"],
        description="Case identifier for grouping experiments..",
    )
)

register_metric(
    MetricSpec(
        key="experiment",
        label="Exp",
        aggregates=["cnt"],
        description="Experiment identifier grouping multiple runs.",
    )
)

register_metric(
    MetricSpec(
        key="run",
        label="Run",
        aggregates=["cnt"],
        description="Run identifier within an experiment.",
    )
)


def _format_run_id(r):
    case = r.get("case")
    exp = r.get("experiment")
    run = r.get("run")

    if case is None or exp is None or run is None:
        return None

    return f"{case}/{exp}/{run}"


register_metric(
    MetricSpec(
        key="run_id_compact",
        label="Case/\n Exp/\nRun",
        dtype=str,
        align="center",
        compute_fn=lambda r: _format_run_id(r),
        description="Compact identifier: case/experiment/run",
    )
)

register_metric(
    MetricSpec(
        key="trial",
        label="Trls",
        aggregates=["cnt"],
        description="Number of simulation trials in the run.",
    )
)


register_metric(
    MetricSpec(
        key="objective",
        path="_inputs.optimization_parameters.objective",
        label="Objective",
        dtype=str,
        description="Optimization objective used in the plan (e.g., maximize spending or bequest).",
    )
)


def _compute_goal_from_inputs(r):
    obj = r.get("objective")

    inputs = r.get("_inputs", {})
    solver = inputs.get("solver_options", {})

    # ----------------------------------------
    # 1. Get raw value
    # ----------------------------------------
    if obj == "maxSpending":
        raw = solver.get("bequest")

    elif obj == "maxBequest":
        raw = solver.get("netSpending")

    else:
        return None

    if raw is None:
        return None

    # ----------------------------------------
    # 2. Normalize units → dollars
    # ----------------------------------------
    units = solver.get("units", "k")  # default k-dollars

    try:
        v = float(raw)
    except Exception:
        return None

    if units == "k":
        return v * 1_000
    elif units == "M":
        return v * 1_000_000
    else:  # "1"
        return v


def _format_goal_and_target(value, row):
    if value is None:
        return "-"

    if not isinstance(row, dict):
        return "-"  # or just return formatted value

    obj = row.get("objective")

    def short_currency(v):
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"${int(v/1000)}K"
        return f"${int(v)}"

    val = short_currency(value)

    if obj == "maxSpending":
        return f"MaxSpnd·Beq={val}"

    if obj == "maxBequest":
        return f"MaxBeq·Spnd={val}"

    return obj or "-"


def _format_goal(value, row):
    if value is None:
        return "-"

    if not isinstance(row, dict):
        return "-"  # or just return formatted value

    obj = row.get("objective")

    if obj == "maxSpending":
        return "MaxSpnd"

    if obj == "maxBequest":
        return "MaxBeq"

    return obj or "-"


register_metric(
    MetricSpec(
        key="goal_and_target",
        label="Goal·\nTarget",
        align="left",
        compute_fn=_compute_goal_from_inputs,
        is_invariant=True,
        description="User-defined optimization goal (constraint target).",
        display_row_fn=lambda v, row, ctx: _format_goal_and_target(v, row),
        value_series_fn=lambda values, rows, *_: (
            _format_goal(values[0], next((r for r in rows if isinstance(r, dict)), {}))
            if values
            else "-"
        ),
    )
)

register_metric(
    MetricSpec(
        key="goal",
        label="Goal",
        align="left",
        compute_fn=_compute_goal_from_inputs,
        is_invariant=True,
        description="User-defined optimization goal (constraint target).",
        display_row_fn=lambda v, row, ctx: _format_goal(v, row),
        value_series_fn=lambda values, rows, *_: (
            _format_goal(values[0], next((r for r in rows if isinstance(r, dict)), {}))
            if values
            else "-"
        ),
    )
)


def _format_number(v):
    try:
        f = float(v)
    except Exception:
        return str(v)

    # remove trailing .0 if integer
    if f.is_integer():
        return str(int(f))

    return str(f)


def _format_rates(r):
    inputs = r.get("_inputs", {})
    rates = inputs.get("rates_selection", {})

    method = rates.get("method")

    # ----------------------------------------
    # Historical bootstrap (SoR)
    # ----------------------------------------
    if method in [
        "historical",
        "historical average",
        "histogaussian",
        "histolognormal",
        "bootstrap_sor",
        "var",
        "garch_dcc",
    ]:
        start = rates.get("from")
        end = rates.get("to")
        short_method = RATES_METHOD_ABBR.get(method, method)
        if start and end:
            return f"{short_method} ({start}–{end})"
        return short_method

    # ----------------------------------------
    # User-defined rates
    # ----------------------------------------
    if method in ["user", "gaussian", "lognormal"]:
        vals = rates.get("values") or []
        if vals:
            vals_str = "/".join(_format_number(v) for v in vals)
            return f"{method} ({vals_str})"
        return f"{method}"

    # ----------------------------------------
    # Fallback
    # ----------------------------------------
    return method or "-"


register_metric(
    MetricSpec(
        key="rates",
        label="Rates",
        align="left",
        compute_fn=_format_rates,
        is_invariant=True,
        description="Compact description of return scenario generation method.",
    )
)


def _compute_rates_method(r):
    rs = r.get("_inputs", {}).get("rates_selection", {})
    return rs.get("method") or "-"


register_metric(
    MetricSpec(
        key="rates_method",
        label="Rates Method",
        dtype=str,
        compute_fn=_compute_rates_method,
        is_invariant=True,
        description="Method used to generate return and inflation scenarios.",
    )
)


def _compute_rates_values(r):
    rs = r.get("_inputs", {}).get("rates_selection", {})

    method = rs.get("method")
    values = rs.get("values")
    from_ = rs.get("from")
    to_ = rs.get("to")

    # --- User-defined rates ---
    if method == "user" and values:
        return ", ".join(str(v) for v in values)

    # --- Historical / bootstrap / ranged methods ---
    if from_ is not None and to_ is not None:
        return f"{from_}–{to_}"

    # --- Fallback ---
    return method or "-"


register_metric(
    MetricSpec(
        key="rates_values",
        label="Rates values",
        dtype=str,
        compute_fn=_compute_rates_values,
        is_invariant=True,
        description="Rates configuration (values for user, or year range for historical methods).",
    )
)

# =========================================================
# OVERRIDES (CONTEXT-BASED — CORRECT IMPLEMENTATION)
# =========================================================


def _flatten_dict(d, prefix=""):
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}.{k}" if prefix else k

        if isinstance(v, dict):
            out.update(_flatten_dict(v, key))
        else:
            out[key] = v

    return out


def _format_override_dict(d: dict | None, row: dict | None = None) -> str:
    if not d:
        return "-"

    flat = _flatten_dict(d)

    lines = []
    used_rates = False
    used_range = False

    # ----------------------------------------
    # Detect if overrides include rates fields
    # ----------------------------------------
    has_rate_override = any(k.startswith("rates_selection.") for k in flat)

    # ----------------------------------------
    # Use precomputed rates ONLY if overridden
    # ----------------------------------------
    if has_rate_override and row:
        rates = row.get("rates_method")
        if rates:
            lines.append(f"method = {rates}")
            used_rates = True
        values = row.get("rates_values")
        if values:
            lines.append(f"values = {values}")
            used_rates = True

    # ----------------------------------------
    # Fallback: combine from/to if no rates string
    # ----------------------------------------
    if has_rate_override and not used_rates:
        from_key = next((k for k in flat if k.endswith(".from")), None)
        to_key = next((k for k in flat if k.endswith(".to")), None)

        if from_key and to_key:
            lines.append(f"from-to = {flat[from_key]}-{flat[to_key]}")
            used_range = True

    # ----------------------------------------
    # Main loop
    # ----------------------------------------
    for k, v in sorted(flat.items()):
        # Skip rate fields if already rendered
        if used_rates and k.startswith("rates_selection."):
            continue

        # Skip from/to if combined
        if used_range and k.endswith((".from", ".to")):
            continue

        # Clean labels
        clean_key = k.replace("solver_options.", "")
        clean_key = clean_key.replace("optimization_parameters.", "")
        clean_key = clean_key.replace("rates_selection.", "")

        lines.append(f"{clean_key} = {v}")

    return "\n".join(lines) if lines else "-"


def _override_value_series_fn(values, raw, rows):
    clean = [v for v in raw if isinstance(v, dict) and v]

    if not clean:
        return "-"

    first = clean[0]
    row = rows[0] if rows else {}

    if all(v == first for v in clean):
        return _format_override_dict(first, row=row)

    # fallback (rare)
    return "\n".join(_format_override_dict(v, row=row) for v in clean[:3])


register_metric(
    MetricSpec(
        key="run_specific_overrides",
        label="Run-specific overrides",
        dtype=dict,
        fmt="overrides",
        is_invariant=True,
        compute_fn=lambda r: r.get("run_specific_overrides"),
        description=(
            "Overrides that vary across runs (e.g., parameter sweeps such as "
            "solver_options.spendingSlack)."
        ),
        display_row_fn=lambda v, row, ctx: _format_override_dict(v, row),
        value_series_fn=_override_value_series_fn,
    )
)


register_metric(
    MetricSpec(
        key="common_overrides",
        label="Common overrides",
        dtype=dict,
        fmt="overrides",
        is_invariant=True,
        compute_fn=lambda r: r.get("common_overrides"),
        description=(
            "Overrides shared across all runs in the experiment "
            "(e.g., rates_selection.method, date ranges)."
        ),
        display_row_fn=lambda v, row, ctx: _format_override_dict(v, row),
        value_series_fn=_override_value_series_fn,
    )
)

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
# RISK
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
        description="Final assets divided by final spending (inverse of spending-to-assets ratio).",
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
        description="Risk classification based on plan outcomes only (ignores scenario severity).",
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
        description="Number of risk signals triggered in scenario and outcome.",
    )
)


def _compute_distribution_risk_flags(r):
    flags = 0

    p10_min = _as_float(r.get("spending_ratio_to_minimum_min_p10"))
    p10_acc = _as_float(r.get("spending_ratio_to_acceptable_min_p10"))
    breach = _as_float(r.get("spending_stress_flag_ratio"))

    if p10_min is not None and p10_min < 1.0:
        flags += 1

    if p10_min is not None and p10_min < 0.5:
        flags += 1

    if p10_acc is not None and p10_acc < 1.0:
        flags += 1

    if breach is not None and breach > 0.1:
        flags += 1

    return flags


def _compute_path_risk_signals(r):
    flags = r.get("risk.summary.flags")
    return flags if isinstance(flags, list) else []


def _compute_distribution_risk_signals(r):
    signals = []

    p10_min = _as_float(r.get("spending_ratio_to_minimum_min_p10"))
    p10_acc = _as_float(r.get("spending_ratio_to_acceptable_min_p10"))
    breach = _as_float(r.get("spending_stress_flag_ratio"))

    years_min = r.get("years_below_minimum_mean")
    years_acc = r.get("years_below_acceptable_mean")

    # --- PRIORITY ORDER ---

    # 1. Severe survival risk (dominates everything)
    if p10_min is not None and p10_min < 0.5:
        return ["Severe depletion risk"]

    # 2. Survival risk
    if p10_min is not None and p10_min < 1.0:
        signals.append("Below minimum in tail scenarios")

    # 3. Persistent survival failure
    if years_min is not None and years_min > 0:
        signals.append("Persistent minimum shortfall")

    # 4. Persistent lifestyle failure
    if years_acc is not None and years_acc > 0:
        signals.append("Sustained lifestyle shortfall")

    # 5. Lifestyle degradation
    if p10_acc is not None and p10_acc < 1.0:
        signals.append("Lifestyle degradation risk")

    # 6. Frequency (only if nothing stronger dominates)
    if breach is not None:
        if breach > 0.9:
            signals.append("Frequent shortfalls")
        elif breach > 0.1:
            signals.append("Occasional shortfalls")

    # --- LIMIT to top 2–3 signals ---
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
        "Severe depletion risk": "Plan fails in worst-case scenarios; survival risk dominates.",
        "Below minimum in tail scenarios": "Plan is vulnerable in adverse scenarios but generally stable.",
        "Persistent minimum shortfall": "Spending falls below minimum for extended periods.",
        "Sustained lifestyle shortfall": "Lifestyle goals are not consistently maintained.",
        "Lifestyle degradation risk": "Spending occasionally falls below target levels.",
        "Frequent shortfalls": "Shortfalls occur across most scenarios.",
        "Occasional shortfalls": "Shortfalls occur in a minority of scenarios.",
    }

    return mapping.get(primary, "Mixed risk signals present.")


def _compute_overall_risk(r):
    survival = _survival_level(r)
    lifestyle = _lifestyle_level(r)

    # --- survival dominates ---
    if survival == "high":
        return "At risk of depletion"

    if survival == "moderate":
        return "At risk"

    # --- lifestyle ---
    if lifestyle == "high":
        return "Severely constrained"

    if lifestyle == "moderate":
        return "Safe but constrained"

    return "Comfortable and safe"


FLAG_EXPLANATIONS = {
    "ending_asset_erosion": (
        "Financial assets decline significantly late in life. This may reflect "
        "planned use or conversion of assets (e.g., home sale), not necessarily risk."
    ),
    "high_spending_pressure": (
        "Spending uses a large portion of financial assets. This may be acceptable "
        "if supported by other assets or planned drawdown."
    ),
    "severe_asset_drawdown": (
        "Financial assets experience large declines. In some plans, this reflects "
        "intentional drawdown or asset conversion rather than adverse outcomes."
    ),
}

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
        display_row_fn=lambda v, row, ctx: (
            "see explain=values" if isinstance(row, dict) and row.get("risk_flags", 0) > 0 else "-"
        ),
        value_series_fn=lambda values, *_: values[0] if values and values[0] else "-",
    )
)


def _lifestyle_level(r):
    p10 = _as_float(r.get("spending_ratio_to_acceptable_min_p10"))
    years = r.get("years_below_acceptable_mean")

    if p10 is not None:
        if p10 < 0.5:
            return "high"
        if p10 < 1.0:
            return "moderate"

    if years is not None and years > 0:
        return "moderate"

    return "low"


def _survival_level(r):
    p10 = _as_float(r.get("spending_ratio_to_minimum_min_p10"))
    years = r.get("years_below_minimum_mean")

    if p10 is not None:
        if p10 < 0.5:
            return "high"
        if p10 < 1.0:
            return "moderate"

    if years is not None and years > 0:
        return "moderate"

    return "low"


def _compute_risk_summary(r):
    survival = _survival_level(r)
    lifestyle = _lifestyle_level(r)

    # --- Defensive fallback ---
    if survival is None and lifestyle is None:
        return "Comfortable and safe"

    # --- Survival dominates everything ---
    if survival == "high":
        return "At risk of depletion"

    # --- Moderate survival ---
    if survival == "moderate":
        # upgrade if lifestyle also stressed
        if lifestyle in ("moderate", "high"):
            return "At risk"
        return "At risk"

    # --- No survival risk → lifestyle determines outcome ---
    if lifestyle == "high":
        return "Severely constrained"

    if lifestyle == "moderate":
        return "Safe but constrained"

    # --- Fully safe ---
    return "Comfortable and safe"


register_metric(
    MetricSpec(
        key="survival_risk",
        label="Survival\nRisk",
        dtype=str,
        compute_level="run",
        compute_fn=_survival_level,
        is_invariant=True,
        description=(
            "Risk of failing to sustain minimum required spending (safety floor). "
            "Based on downside (p10) outcomes and frequency of years below minimum spending. "
            "Represents fundamental survival risk — whether essential expenses can be met."
        ),
        value_series_fn=lambda values, *_: values[0] if values and values[0] else "-",
    )
)

register_metric(
    MetricSpec(
        key="lifestyle_risk",
        label="Lifestyle\nRisk",
        dtype=str,
        compute_level="run",
        compute_fn=_lifestyle_level,
        is_invariant=True,
        description=(
            "Risk of failing to sustain acceptable lifestyle spending. "
            "Based on downside (p10) outcomes and frequency of years below acceptable spending. "
            "Represents quality-of-life risk — whether desired spending levels are maintained."
        ),
        value_series_fn=lambda values, *_: values[0] if values and values[0] else "-",
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
        description=(
            "Composite risk classification based on downside (p10) spending outcomes and "
            "frequency of spending shortfalls relative to acceptable and minimum levels. "
            "Captures both survival risk (failure scenarios) and lifestyle risk (reduced spending)."
        ),
    )
)

# =========================================================
# SPENDING STRESS (PRECOMPUTED)
# =========================================================

register_metric(
    MetricSpec(
        key="minimum_spending",
        path="financial.spending_policy.minimum_spending",
        label="Minimum\nspending",
        fmt="currency",
        dtype=float,
        is_invariant=True,
        description="Minimum lifestyle spending level (safety, user-input).",
    )
)

register_metric(
    MetricSpec(
        key="acceptable_spending",
        path="financial.spending_policy.acceptable_spending",
        label="Acceptable\nspending",
        fmt="currency",
        dtype=float,
        is_invariant=True,
        description="Base acceptable spending level (scaled by household profile over time).",
    )
)


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
# MINIMUM SPENDING (FLOOR SAFETY)
# =========================================================

register_metric(
    MetricSpec(
        key="spending_ratio_to_minimum_min",
        path="financial.spending_summary.min_ratio_to_minimum",
        label="Worst Year/\nMinimum",
        fmt="percent2",
        aggregates=["mean", "p10"],
        description="Lowest spending relative to minimum spending (safety).",
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "Falls below minimum spending"
                if v < 1
                else f"Always above minimum spending (min {format_value(v, 'percent2')})"
            )
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_minimum_mean",
        path="financial.spending_summary.mean_ratio_to_minimum",
        label="Avg Year/\nMinimum",
        fmt="percent2",
        aggregates=["mean"],
        description="Average spending relative to minimum spending.",
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_minimum_median",
        path="financial.spending_summary.median_ratio_to_minimum",
        label="Median Year/\nMinimum",
        fmt="percent2",
        aggregates=["mean"],
        description="Median spending relative to minimum spending.",
    )
)

register_metric(
    MetricSpec(
        key="years_below_minimum",
        path="financial.spending_summary.years_below_minimum",
        label="Years\n< Minimum",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Number of years spending falls below minimum spending level.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years below minimum spending"),
    )
)

register_metric(
    MetricSpec(
        key="consecutive_years_below_minimum",
        path="financial.spending_summary.consecutive_years_below_minimum",
        label="Consec <\nMinimum",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Maximum consecutive years spending falls below minimum spending level.",
        value_series_fn=wrap_value_fn(
            lambda v, _: f"{int(v)} consecutive years below minimum spending"
        ),
    )
)

register_metric(
    MetricSpec(
        key="floor_breach",
        path="financial.spending_summary.floor_breach",
        label="Minimum\nBreach",
        dtype=int,
        fmt="count_ratio",
        aggregates=[("ratio", "count_ratio")],
        description="Number of trials where spending falls below minimum spending at any year of trial.",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Minimum breached", "Minimum never breached")
        ),
    )
)

# =========================================================
# ACCEPTABLE SPENDING (BEHAVIORAL TOLERANCE)
# =========================================================

register_metric(
    MetricSpec(
        key="spending_ratio_to_acceptable_min",
        path="financial.spending_summary.min_ratio_to_acceptable",
        label="Worst Year/\nAcceptable",
        fmt="percent2",
        aggregates=["mean", "p10"],
        description="Lowest spending relative to acceptable lifestyle (adjusted for household size via xi_n).",
        value_series_fn=wrap_value_fn(
            lambda v, _: (
                "Below acceptable lifestyle"
                if v < 1
                else f"Maintains acceptable level (min {format_value(v, 'percent2')})"
            )
        ),
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_acceptable_mean",
        path="financial.spending_summary.mean_ratio_to_acceptable",
        label="Avg Year/\nAcceptable",
        fmt="percent2",
        aggregates=["mean"],
        description="Average spending relative to acceptable level.",
    )
)

register_metric(
    MetricSpec(
        key="spending_ratio_to_acceptable_median",
        path="financial.spending_summary.median_ratio_to_acceptable",
        label="Median Year/\nAcceptable",
        fmt="percent2",
        aggregates=["mean"],
        description="Median spending relative to acceptable level.",
    )
)

register_metric(
    MetricSpec(
        key="years_below_acceptable",
        path="financial.spending_summary.years_below_acceptable",
        label="Years <\nAcceptable",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Number of years spending falls below acceptable level.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years below acceptable spending"),
    )
)

register_metric(
    MetricSpec(
        key="consecutive_years_below_acceptable",
        path="financial.spending_summary.consecutive_years_below_acceptable",
        label="Consec <\nAcceptable",
        fmt="int",
        aggregates=["mean", "p90"],
        description="Maximum consecutive years below acceptable spending.",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} consecutive years below acceptable"),
    )
)

register_metric(
    MetricSpec(
        key="spending_stress_flag",
        path="financial.spending_summary.spending_stress_flag",
        label="Acceptable\nBreach",
        dtype=int,
        fmt="count_ratio",
        aggregates=[("ratio", "count_ratio")],
        description="Number of trials where spending falls below acceptable level at any year in trial.",
        value_series_fn=wrap_value_fn(
            lambda v, _: _bool_value(v == 1, "Stress triggered", "No stress")
        ),
    )
)

# =========================================================
# SPENDING - worst spending avlue
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
        fmt="currency",  # ✅ now works
        aggregates=["mean", "median", "p90"],  # safe even for 1 trial
        compute_fn=_compute_spending_worst,
        description=(
            "Lowest annual spending observed across the plan horizon, "
            "measured in today's dollars."
        ),
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
        key="years_between_min_and_target",
        path="financial.spending_summary.years_between_min_and_target",
        label="Years\nAdaptive",
        fmt="int",
        aggregates=["mean"],
        description="Years where spending is below target but above minimum (adaptive zone).",
        value_series_fn=wrap_value_fn(lambda v, _: f"{int(v)} years in adaptive zone"),
    )
)

# =========================================================
# RUN PROFILING / DASHBOARD FLAGS
# =========================================================


def _has_override(r, key_fragment: str) -> bool:
    overrides = r.get("run_specific_overrides") or {}
    return any(key_fragment in k for k in overrides)


def _run_variation_profile(r):
    flags = []

    overrides = r.get("run_specific_overrides") or {}

    if any("social_security_ages" in k for k in overrides):
        flags.append("SS")

    if any("spendingSlack" in k for k in overrides):
        flags.append("Slack")

    if any("roth" in k.lower() for k in overrides):
        flags.append("Roth")

    return ", ".join(flags) if flags else "Base"


def _run_scenario_profile(r):
    method = r.get("rates_method")

    if method == "bootstrap_sor":
        return "SoR"

    if method == "user":
        return "UserRates"

    if method:
        return method

    return "-"


register_metric(
    MetricSpec(
        key="run_variation_profile",
        label="Design",
        align="left",
        dtype=str,
        compute_level="run",
        compute_fn=_run_variation_profile,
        is_invariant=True,
        description="Parameters varied across runs (experiment design)",
    )
)

register_metric(
    MetricSpec(
        key="run_scenario_profile",
        label="Scenario",
        align="left",
        dtype=str,
        compute_level="run",
        compute_fn=_run_scenario_profile,
        is_invariant=True,
        description="Scenario model used for evaluation (e.g., SoR, user-defined)",
    )
)


def _run_profile(r):
    flags = []

    overrides = r.get("run_specific_overrides") or {}

    if "social_security_ages" in overrides:
        flags.append("SS")

    if "solver_options.spendingSlack" in overrides:
        flags.append("Slack")

    if r.get("rates_method") == "bootstrap_sor":
        flags.append("SoR")

    if any("roth" in k for k in overrides):
        flags.append("Roth")

    return ", ".join(flags) if flags else "Base"


register_metric(
    MetricSpec(
        key="run_profile",
        label="Profile",
        align="left",
        dtype=str,
        compute_level="run",
        compute_fn=_run_profile,
        is_invariant=True,
        description="High-level classification of the experiment intent",
    )
)


# ---------------------------------------------------------
# INDIVIDUAL FLAGS (yes / -)
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="is_ss_experiment",
        label="SS",
        dtype=int,
        compute_level="run",
        compute_fn=lambda r: 1 if _has_override(r, "social_security_ages") else 0,
        value_series_fn=wrap_value_fn(lambda v, _: "yes" if v == 1 else "-"),
        description="Run varies Social Security claiming strategy",
    )
)

register_metric(
    MetricSpec(
        key="is_spending_slack",
        label="Slack",
        dtype=int,
        compute_level="run",
        compute_fn=lambda r: 1 if _has_override(r, "spendingSlack") else 0,
        value_series_fn=wrap_value_fn(lambda v, _: "yes" if v == 1 else "-"),
        description="Run explores spending flexibility",
    )
)

register_metric(
    MetricSpec(
        key="is_sor_experiment",
        label="SoR",
        dtype=int,
        compute_level="run",
        compute_fn=lambda r: 1 if r.get("rates_method") == "bootstrap_sor" else 0,
        value_series_fn=wrap_value_fn(lambda v, _: "yes" if v == 1 else "-"),
        description="Run explores sequence-of-returns risk",
    )
)

register_metric(
    MetricSpec(
        key="is_roth_strategy",
        label="Roth",
        dtype=int,
        compute_level="run",
        compute_fn=lambda r: 1 if _has_override(r, "roth") else 0,
        value_series_fn=wrap_value_fn(lambda v, _: "yes" if v == 1 else "-"),
        description="Run explores Roth conversion or tax strategy",
    )
)

register_metric(
    MetricSpec(
        key="has_overrides",
        label="Varies",
        dtype=int,
        compute_level="run",
        compute_fn=lambda r: 1 if (r.get("run_specific_overrides") or {}) else 0,
        value_series_fn=wrap_value_fn(lambda v, _: "yes" if v == 1 else "-"),
        description="Run varies one or more key inputs",
    )
)


# ---------------------------------------------------------
# ATTENTION / QUALITY FLAGS
# ---------------------------------------------------------


def _needs_attention(r):
    """
    Conservative flag:
    highlight anything that deserves a closer look.
    """
    if r.get("solver_fail"):
        return 1

    if r.get("floor_breach"):
        return 1

    ratio = r.get("spending_ratio_min")
    if ratio is not None and ratio < 0.85:
        return 1

    return 0


def _bad_run(r):
    """
    Strong failure flag:
    clearly unacceptable plans.
    """
    if r.get("solver_fail"):
        return 1

    if r.get("floor_breach"):
        return 1

    ratio = r.get("spending_ratio_min")
    if ratio is not None and ratio < 0.70:
        return 1

    return 0


register_metric(
    MetricSpec(
        key="needs_attention",
        label="Review",
        dtype=int,
        compute_fn=_needs_attention,
        compute_level="run",
        aggregates=[("cnt_true", "int"), ("pct", "percent")],
        description="Run shows warning signs and should be reviewed",
        value_series_fn=wrap_value_fn(lambda v, _: "⚠️ yes" if v == 1 else "-"),
    )
)

register_metric(
    MetricSpec(
        key="bad_run_flag",
        label="Bad",
        dtype=int,
        compute_fn=_bad_run,
        compute_level="run",
        aggregates=[("cnt_true", "int"), ("pct", "percent")],
        description="Run is clearly unacceptable (failure or severe spending collapse)",
        value_series_fn=wrap_value_fn(lambda v, _: "❌ yes" if v == 1 else "-"),
    )
)


def _run_status(r):
    if r.get("solver_fail"):
        return "Fail"

    if r.get("floor_breach"):
        return "Below minimum"

    ratio = r.get("spending_ratio_min")

    if ratio is not None:
        if ratio < 0.70:
            return "Collapse"
        if ratio < 0.85:
            return "Stress"

    return "✓ OK"


register_metric(
    MetricSpec(
        key="run_status_summary",
        label="Status",
        dtype=str,
        compute_fn=_run_status,
        compute_level="run",
        description="Overall run quality classification (fail, stress, ok)",
    )
)
