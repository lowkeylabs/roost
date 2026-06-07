# tests/metrics/test_plugin_registration.py

from __future__ import annotations

from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)
from owlroost.metrics.specs import (
    MetricSpec,
)

# =========================================================
# Registry Build
# =========================================================


def test_all_metrics_plugins_register():
    """
    Ensure all metrics plugins successfully
    register into the unified metrics
    ontology registry.

    This acts as a high-level integration
    contract test across all metrics plugins.
    """

    registry = build_metrics_registry()

    metrics = list(registry.all())

    assert metrics


# =========================================================
# Ontology Type Integrity
# =========================================================


def test_all_registered_metrics_are_metricspec():
    """
    Ensure all registered ontology entries
    are canonical MetricSpec instances.
    """

    registry = build_metrics_registry()

    for metric in registry.all():
        assert isinstance(
            metric,
            MetricSpec,
        )


# =========================================================
# Modern Ontology Vocabulary
# =========================================================


def test_no_legacy_level_attribute():
    """
    Prevent regressions back to the legacy
    ontology vocabulary.

    Metric ontology should use:

        materialization_level

    rather than:

        level
    """

    registry = build_metrics_registry()

    for metric in registry.all():
        assert not hasattr(
            metric,
            "level",
        )


# =========================================================
# Materialization Integrity
# =========================================================


def test_all_metrics_have_materialization_level():
    """
    Every metric ontology field should
    declare analytical materialization
    semantics.
    """

    registry = build_metrics_registry()

    for metric in registry.all():
        assert metric.materialization_level is not None


# =========================================================
# Projection Integrity
# =========================================================


def test_all_metrics_have_projection_kind():
    """
    Every metric ontology field should
    declare projection semantics.
    """

    registry = build_metrics_registry()

    for metric in registry.all():
        assert metric.projection_kind is not None


# =========================================================
# Canonical Identity Integrity
# =========================================================


def test_metric_names_are_unique():
    """
    Canonical metric ontology names must
    be globally unique.
    """

    registry = build_metrics_registry()

    names = [metric.name for metric in registry.all()]

    assert len(names) == len(set(names))


# =========================================================
# Description Integrity
# =========================================================


def test_all_metrics_have_description():
    """
    Ensure metric ontology fields expose
    explainability metadata.
    """

    registry = build_metrics_registry()

    for metric in registry.all():
        assert metric.description is not None


# =========================================================
# Aggregate Ontology Integrity
# =========================================================


def test_aggregate_definitions_are_normalized():
    """
    Aggregate ontology definitions should
    use normalized aggregate specifications.
    """

    registry = build_metrics_registry()

    for metric in registry.all():
        if not metric.default_aggregates:
            continue

        for aggregate in metric.default_aggregates:
            assert isinstance(
                aggregate,
                str,
            ) or isinstance(
                aggregate,
                tuple,
            )


# =========================================================
# Aggregate Projection Eligibility
# =========================================================


def test_trial_metrics_support_aggregation():
    """
    Aggregatable trial metrics should expose
    aggregate ontology projections.
    """

    registry = build_metrics_registry()

    trial_metrics = [
        metric for metric in registry.all() if (metric.materialization_level == "trial")
    ]

    assert trial_metrics

    for metric in trial_metrics:
        if metric.aggregatable:
            assert metric.default_aggregates


# =========================================================
# Ownership Integrity
# =========================================================


def test_all_metrics_have_owner():
    """
    Every metric ontology field should
    declare semantic ownership.
    """

    registry = build_metrics_registry()

    for metric in registry.all():
        assert metric.owner
