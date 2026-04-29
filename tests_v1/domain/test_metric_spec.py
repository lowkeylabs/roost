from owlroost.domain.metrics.metric_spec import MetricSpec


def test_extract_simple_path():
    spec = MetricSpec(
        key="test",
        path="a.b.c",
        label="Test",
    )

    data = {"a": {"b": {"c": 42}}}
    assert spec.extract(data) == 42


def test_extract_missing_path_returns_none():
    spec = MetricSpec(
        key="test",
        path="a.b.c",
        label="Test",
    )

    data = {"a": {}}
    assert spec.extract(data) is None


def test_compute_fn_overrides_path():
    spec = MetricSpec(
        key="computed",
        label="Computed",
        compute_fn=lambda d: d.get("x", 0) + 1,
    )

    data = {"x": 5}
    assert spec.extract(data) == 6
