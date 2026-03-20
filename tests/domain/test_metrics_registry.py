import pytest

from owlroost.domain.metrics.metric_registry import METRIC_REGISTRY, get_metric


def test_metrics_are_registered():
    # Basic sanity check
    assert len(METRIC_REGISTRY) > 0


def test_known_metric_exists():
    m = get_metric("bequest")
    assert m.key == "bequest"
    assert m.path == "financial.bequest.total.today"


def test_duplicate_metric_registration_raises():
    from owlroost.domain.metrics.metric_registry import register_metric
    from owlroost.domain.metrics.metric_spec import MetricSpec

    with pytest.raises(ValueError):
        register_metric(
            MetricSpec(
                key="bequest",  # already exists
                path="x",
                label="Duplicate",
            )
        )
