from owlroost.domain.metrics.metric_spec import MetricSpec

TRIAL_VIEW = [
    MetricSpec(
        key="status",
        path="run_status.status",
        label="Status",
        dtype=str,
        align="left",
    ),
    MetricSpec(
        key="elapsed",
        path="timing.elapsed_seconds",
        label="Time (s)",
        fmt="float2",
    ),
    MetricSpec(
        key="spending",
        path="financial.spending.total.today",
        label="Spending",
        fmt="currency",
    ),
    MetricSpec(
        key="bequest",
        path="financial.bequest.total.today",
        label="Bequest",
        fmt="currency",
    ),
    MetricSpec(
        key="risk",
        path="risk.outcome.classification.risk_level",
        label="Risk",
        dtype=str,
    ),
]
