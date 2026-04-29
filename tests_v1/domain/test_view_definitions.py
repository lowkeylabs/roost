from owlroost.domain.metrics.view_registry import METRIC_VIEW_REGISTRY


def test_views_registered():
    assert "trial" in METRIC_VIEW_REGISTRY
    assert "run" in METRIC_VIEW_REGISTRY

    assert "default" in METRIC_VIEW_REGISTRY["trial"]
    assert "default" in METRIC_VIEW_REGISTRY["run"]


def test_trial_view_keys_are_strings():
    keys = METRIC_VIEW_REGISTRY["trial"]["default"]

    assert all(isinstance(k, str) for k in keys)
