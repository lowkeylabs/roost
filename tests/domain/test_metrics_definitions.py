from owlroost.domain.metrics.metric_registry import METRIC_REGISTRY


def test_expected_metrics_present():
    expected = [
        "status",
        "elapsed",
        "bequest",
        "spending_total",
        "risk",
        "ending_assets",
        "min_cushion",
        "worst_drawdown",
        "terminal_ratio",
    ]

    for key in expected:
        assert key in METRIC_REGISTRY, f"Missing metric: {key}"


def test_aggregates_defined_for_key_metrics():
    bequest = METRIC_REGISTRY["bequest"]
    assert "mean" in bequest.aggregates
    assert "median" in bequest.aggregates
