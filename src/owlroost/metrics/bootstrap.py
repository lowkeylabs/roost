# src/owlroost/metrics/registry/bootstrap.py

from owlroost.metrics.plugins.output_metrics import (
    OutputMetricsPlugin,
)
from owlroost.metrics.registry import (
    MetricsRegistry,
)

# =========================================================
# Bootstrap
# =========================================================


def build_metrics_registry():
    """
    Construct MetricsRegistry.

    MetricsRegistry defines the canonical
    semantic model for OUTPUT metrics.

    This registry is intentionally independent
    from runtime metric generation.

    Responsibilities:
        - metric names
        - dtypes
        - descriptions
        - aggregation defaults
        - compute levels
        - display hints

    Runtime metric synthesis belongs to:

        metrics/builders.py
    """

    reg = MetricsRegistry()

    # =====================================================
    # Register canonical output metrics
    # =====================================================

    OutputMetricsPlugin().register(
        reg,
    )

    return reg
