import pytest

from owlroost.domain.metrics.view_registry import get_view, list_views


def test_default_trial_view_exists():
    views = list_views("trial")
    assert "default" in views


def test_get_trial_view_returns_specs():
    view, layout = get_view("trial", "default")

    assert len(view) > 0
    for spec in view:
        assert hasattr(spec, "key")


def test_get_run_view_returns_specs():
    view, layout = get_view("run", "default")

    assert len(view) > 0
    for spec in view:
        assert hasattr(spec, "key")


def test_invalid_view_raises():
    with pytest.raises(KeyError):
        _v, _l = get_view("trial", "nonexistent")
