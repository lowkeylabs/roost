# src/owlroost/domain/metrics/definitions/inputs.py

from ..metric_registry import register_metric
from ..metric_spec import MetricSpec
from ..utils import RATES_METHOD_ABBR

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


# =========================================================
# trials
# =========================================================

register_metric(
    MetricSpec(
        key="trial",
        label="Trls",
        dtype=str,
        compute_level="trial",
        compute_fn=lambda r: r.get("trial_id"),
        aggregates=["cnt"],
        description="Trial identifier (aggregated count gives number of trials).",
    )
)

register_metric(
    MetricSpec(
        key="trials_completed",
        label="Trls (done)",
        compute_level="run",
        compute_fn=lambda r: len(r.get("_ctx", {}).get("trial_rows", [])),
        description="Number of completed simulation trials.",
    )
)


def _compute_requested_trials(r):
    # Try overrides first (most reliable)
    val = (r.get("_inputs", {}) or {}).get("trial", {}).get("count")

    if val is not None:
        try:
            return int(val)
        except Exception:
            pass

    # fallback: raw overrides (string-based)
    raw = (r.get("_inputs", {}) or {}).get("roost", {}) or {}
    if "trials" in raw:
        try:
            return int(raw["trials"])
        except Exception:
            pass

    return None


register_metric(
    MetricSpec(
        key="trials_requested",
        label="Trls",
        dtype=int,
        compute_fn=_compute_requested_trials,
        is_invariant=True,
        description="Requested number of simulation trials (from input configuration).",
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
        return f"MxSpd·Beq={val}"

    if obj == "maxBequest":
        return f"MxBeq·Spnd={val}"

    return obj or "-"


def _format_goal(value, row):
    if value is None:
        return "-"

    if not isinstance(row, dict):
        return "-"  # or just return formatted value

    obj = row.get("objective")

    if obj == "maxSpending":
        return "MxSpd"

    if obj == "maxBequest":
        return "MxBeq"

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
        key="input_rates",
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
        key="input_rates_method",
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
        key="input_rates_values",
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
        rates = row.get("input_rates_method")
        if rates:
            lines.append(f"method = {rates}")
            used_rates = True
        values = row.get("input_rates_values")
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
        align="right",
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
        align="right",
        compute_fn=lambda r: r.get("common_overrides"),
        description=(
            "Overrides shared across all runs in the experiment "
            "(e.g., rates_selection.method, date ranges)."
        ),
        display_row_fn=lambda v, row, ctx: _format_override_dict(v, row),
        value_series_fn=_override_value_series_fn,
    )
)

register_metric(
    MetricSpec(
        key="signature",
        label="Signature",
        dtype=str,
        compute_level="run",
        wrap=50,
        compute_fn=lambda r: getattr(r, "signature", None),
        description="Run signature (normalized configuration + execution identity).",
    )
)
