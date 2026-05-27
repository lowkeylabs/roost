from __future__ import annotations

from owlroost.metrics.specs import (
    MetricFieldSpec,
)


# =========================================================
# Construction
# =========================================================


def test_metric_spec_minimal_construction():

    m = MetricFieldSpec(
        name="timing.elapsed_seconds",
    )

    assert (
        m.name
        == "timing.elapsed_seconds"
    )

    assert m.dtype is object

    assert m.aggregatable is True

    assert (
        m.default_aggregates
        == []
    )


# =========================================================
# Ontology Inheritance
# =========================================================


def test_metric_spec_inherits_ontology():

    m = MetricFieldSpec(
        name="timing.elapsed_seconds",
        owner="ROOST",
        semantic_domain="execution",
        value_origin="roost-computed",
        projection_kind="canonical",
        materialization_level="trial",
    )

    assert m.owner == "ROOST"

    assert (
        m.semantic_domain
        == "execution"
    )

    assert (
        m.value_origin
        == "roost-computed"
    )

    assert (
        m.projection_kind
        == "canonical"
    )

    assert (
        m.materialization_level
        == "trial"
    )


# =========================================================
# Aggregate Metadata
# =========================================================


def test_metric_spec_aggregate_metadata():

    m = MetricFieldSpec(
        name="timing.elapsed_seconds__median",
        projection_kind="aggregate",
        aggregate_function="median",
    )

    assert (
        m.projection_kind
        == "aggregate"
    )

    assert (
        m.aggregate_function
        == "median"
    )


# =========================================================
# Mutable Defaults
# =========================================================


def test_metric_profiles_are_isolated():

    a = MetricFieldSpec(
        name="a",
    )

    b = MetricFieldSpec(
        name="b",
    )

    a.profiles["table"] = "x"

    assert "table" not in b.profiles


def test_metric_aggregates_are_isolated():

    a = MetricFieldSpec(
        name="a",
    )

    b = MetricFieldSpec(
        name="b",
    )

    a.default_aggregates.append(
        "median"
    )

    assert (
        b.default_aggregates
        == []
    )


def test_metric_derived_from_isolated():

    a = MetricFieldSpec(
        name="a",
    )

    b = MetricFieldSpec(
        name="b",
    )

    a.derived_from.append(
        "base.metric"
    )

    assert (
        b.derived_from
        == []
    )
