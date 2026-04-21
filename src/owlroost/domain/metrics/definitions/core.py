# src/owlroost/domain/metrics/definitions/core.py

from ...formatting import format_value
from ..metric_registry import register_metric
from ..metric_spec import MetricSpec
from ..utils import wrap_value_fn, _as_float, _bool_value

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

