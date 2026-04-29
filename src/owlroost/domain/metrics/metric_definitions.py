# src/owlroost/domain/metrics/metric_definitions.py

from .metric_registry import register_metric
from .metric_spec import MetricSpec
from .utils import wrap_value_fn

# =========================================================
# Helpers
# =========================================================


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
    method = r.get("input_rates_method")

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
        align="right",
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
        align="right",
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

    if r.get("input_rates_method") == "bootstrap_sor":
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
        compute_fn=lambda r: 1 if r.get("input_rates_method") == "bootstrap_sor" else 0,
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

    if r.get("essential_spending_breach"):
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

    if r.get("essential_spending_breach"):
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

    if r.get("essential_spending_breach"):
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
