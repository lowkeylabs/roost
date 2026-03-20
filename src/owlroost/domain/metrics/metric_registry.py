from .metric_spec import MetricSpec

METRIC_REGISTRY: dict[str, MetricSpec] = {}


def register_metric(spec: MetricSpec):
    if spec.key in METRIC_REGISTRY:
        raise ValueError(f"Duplicate metric key: {spec.key}")

    METRIC_REGISTRY[spec.key] = spec


def get_metric(key: str) -> MetricSpec:
    return METRIC_REGISTRY[key]
