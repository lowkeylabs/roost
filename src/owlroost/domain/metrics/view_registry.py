from dataclasses import dataclass

from .metric_registry import METRIC_REGISTRY, get_metric
from .metric_spec import MetricSpec

METRIC_VIEW_REGISTRY: dict[str, dict[str, list[str]]] = {
    "trial": {},
    "run": {},
    "experiments": {},
}


@dataclass
class ResolvedMetric:
    spec: MetricSpec
    aggregate: str | None = None

    # -----------------------------
    # Core identity
    # -----------------------------
    @property
    def key(self):
        return self.spec.key

    # -----------------------------
    # Display
    # -----------------------------
    @property
    def label(self):
        if self.aggregate:
            return f"{self.spec.label}\n({self.aggregate})"
        return self.spec.label

    @property
    def align(self):
        return self.spec.align

    @property
    def fmt(self):
        return self.spec.fmt

    @property
    def dtype(self):
        return self.spec.dtype


def register_view(level: str, name: str, metric_keys: list[str]):
    METRIC_VIEW_REGISTRY[level][name] = metric_keys


def get_view(level: str, name: str):
    keys = METRIC_VIEW_REGISTRY[level][name]

    resolved = []
    missing = []

    for k in keys:
        # Aggregate metric
        if isinstance(k, tuple):
            base, agg = k

            if base not in METRIC_REGISTRY:
                missing.append(k)
                continue

            spec = get_metric(base)

            if agg not in (spec.aggregates or []):
                raise KeyError(f"Metric '{base}' does not support aggregate '{agg}'")

            resolved.append(ResolvedMetric(spec, agg))

        # Simple metric
        else:
            if k not in METRIC_REGISTRY:
                missing.append(k)
                continue

            resolved.append(ResolvedMetric(get_metric(k)))

    if missing:
        raise KeyError(f"View '{level}:{name}' references unknown metrics: {missing}")

    return resolved


def list_views(level: str):
    return list(METRIC_VIEW_REGISTRY[level].keys())


def resolve_metric(key):
    # aggregate form: ("bequest", "mean")
    if isinstance(key, tuple):
        base, agg = key
        spec = get_metric(base)
        return (spec, agg)

    return (get_metric(key), None)
