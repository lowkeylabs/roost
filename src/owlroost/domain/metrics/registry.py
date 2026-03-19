# domain/metrics/registry.py (next step)

from .metric_spec import MetricSpec

METRIC_SPECS = [
    # -------------------------------------------------
    # Timing
    # -------------------------------------------------
    MetricSpec(
        key="elapsed",
        path="timing.elapsed_seconds",
        label="Time (s)",
        fmt="float2",
        category="timing",
    ),
    # -------------------------------------------------
    # Status
    # -------------------------------------------------
    MetricSpec(
        key="status",
        path="run_status.status",
        label="Status",
        dtype=str,
        category="status",
    ),
    # -------------------------------------------------
    # Financial
    # -------------------------------------------------
    MetricSpec(
        key="spending_today",
        path="financial.spending.total.today",
        label="Spending",
        fmt="currency",
        category="financial",
    ),
    MetricSpec(
        key="bequest_today",
        path="financial.bequest.total.today",
        label="Bequest",
        fmt="currency",
        category="financial",
    ),
    # -------------------------------------------------
    # Risk
    # -------------------------------------------------
    MetricSpec(
        key="risk_level",
        path="risk.outcome.classification.risk_level",
        label="Risk",
        dtype=str,
        category="risk",
    ),
]
