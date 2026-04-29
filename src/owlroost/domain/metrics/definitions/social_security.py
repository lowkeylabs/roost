# domain/metrics/definitions/social_security.py

from ...formatting import format_value
from ..metric_definitions import wrap_value_fn
from ..metric_registry import register_metric
from ..metric_spec import MetricSpec

# ---------------------------------------------------------
# SOCIAL SECURITY STRATEGY
# ---------------------------------------------------------

register_metric(
    MetricSpec(
        key="ss_age_p1",
        label="SS Age\n(P1)",
        dtype=float,
        fmt="age_ym",
        compute_fn=lambda r: (
            r["social_security"]["ages"][0]
            if (
                r.get("social_security")
                and r["social_security"].get("ages")
                and len(r["social_security"]["ages"]) > 0
            )
            else None
        ),
        aggregates=["median", "p10", "p90"],
        description=(
            "Optimized Social Security claiming age for household member 1. "
            "Reported as years and months. Distribution reflects variation across trials."
        ),
        display_row_fn=lambda v, row, *_: (
            f"{row.get('_inputs', {}).get('basic_info', {}).get('names', ['P1'])[0]} "
            f"{format_value(v, 'age_ym')}"
            if v is not None
            else "-"
        ),
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Typical claiming age {format_value(v, 'age_ym')}"
        ),
    )
)

register_metric(
    MetricSpec(
        key="ss_age_p2",
        label="SS Age\n(P2)",
        dtype=float,
        fmt="age_ym",
        compute_fn=lambda r: (
            r["social_security"]["ages"][1]
            if (
                r.get("social_security")
                and r["social_security"].get("ages")
                and len(r["social_security"]["ages"]) > 1
            )
            else None
        ),
        aggregates=["median", "p10", "p90"],
        description=(
            "Optimized Social Security claiming age for household member 2. "
            "Reported as years and months. Distribution reflects variation across trials."
        ),
        display_row_fn=lambda v, row, *_: (
            f"{row.get('_inputs', {}).get('basic_info', {}).get('names', ['P1','P2'])[1]} "
            f"{format_value(v, 'age_ym')}"
            if v is not None
            else "-"
        ),
        value_series_fn=wrap_value_fn(
            lambda v, _: f"Typical claiming age {format_value(v, 'age_ym')}"
        ),
    )
)

register_metric(
    MetricSpec(
        key="ss_input_p1",
        label="SS Input\n(P1)",
        dtype=float,
        fmt="age_ym",
        is_invariant=True,
        compute_fn=lambda r: (
            (r.get("_inputs", {}).get("fixed_income", {}).get("social_security_ages") or [None])[0]
        ),
        description=(
            "User-specified Social Security claiming age for household member 1. "
            "Invariant across trials within a run."
        ),
        value_series_fn=lambda values, *_: (format_value(values[0], "age_ym") if values else "-"),
    )
)

register_metric(
    MetricSpec(
        key="ss_input_p2",
        label="SS Input\n(P2)",
        dtype=float,
        fmt="age_ym",
        is_invariant=True,
        compute_fn=lambda r: (
            (
                r.get("_inputs", {}).get("fixed_income", {}).get("social_security_ages")
                or [None, None]
            )[1]
        ),
        description=(
            "User-specified Social Security claiming age for household member 2. "
            "Invariant across trials within a run."
        ),
        value_series_fn=lambda values, *_: (format_value(values[0], "age_ym") if values else "-"),
    )
)


def compute_opt_ss(r):
    trials = (r.get("_ctx") or {}).get("trial_rows") or []

    for t in trials:
        mode = t.get("_inputs", {}).get("solver_options", {}).get("withSSAges")

        if mode not in (None, "fixed", "none", False):
            return 1

    return 0


register_metric(
    MetricSpec(
        key="is_ss_experiment",
        label="Opt\nSS?",
        dtype=int,
        compute_level="run",
        is_invariant=True,
        compute_fn=lambda r: compute_opt_ss(r),
        display_row_fn=lambda v, *_: "Yes" if v == 1 else "-",
        description=(
            "Indicates whether Social Security claiming ages are being optimized "
            "for one or more household members in this run."
        ),
        value_series_fn=wrap_value_fn(lambda v, _: "Yes" if v == 1 else "-"),
    )
)
