from __future__ import annotations

from owlroost.schema.specs import (
    FieldSpec,
)


# =========================================================
# Construction
# =========================================================


def test_fieldspec_minimal_construction():

    f = FieldSpec(
        name="solver_options.bequest",
    )

    assert (
        f.name
        == "solver_options.bequest"
    )

    assert f.dtype is object

    assert f.path == ()

    assert f.source == "input"


# =========================================================
# Ontology Inheritance
# =========================================================


def test_fieldspec_inherits_ontology():

    f = FieldSpec(
        name="solver_options.bequest",
        owner="OWL",
        semantic_domain="decision",
        value_origin="user-specified",
        projection_kind="canonical",
        materialization_level="run",
    )

    assert f.owner == "OWL"

    assert (
        f.semantic_domain
        == "decision"
    )

    assert (
        f.value_origin
        == "user-specified"
    )

    assert (
        f.projection_kind
        == "canonical"
    )

    assert (
        f.materialization_level
        == "run"
    )


# =========================================================
# Path Normalization
# =========================================================


def test_fieldspec_none_path_becomes_empty_tuple():

    f = FieldSpec(
        name="solver_options.bequest",
        path=None,
    )

    assert f.path == ()


# =========================================================
# Projection Defaults
# =========================================================


def test_fieldspec_default_projection_kind():

    f = FieldSpec(
        name="solver_options.bequest",
    )

    assert (
        f.projection_kind
        == "canonical"
    )


# =========================================================
# Mutable Defaults
# =========================================================


def test_fieldspec_profiles_are_isolated():

    a = FieldSpec(
        name="a",
    )

    b = FieldSpec(
        name="b",
    )

    a.profiles["table"] = "x"

    assert "table" not in b.profiles


def test_fieldspec_aggregates_are_isolated():

    a = FieldSpec(
        name="a",
    )

    b = FieldSpec(
        name="b",
    )

    a.aggregates.append(
        "median"
    )

    assert (
        b.aggregates == []
    )


def test_fieldspec_derived_from_isolated():

    a = FieldSpec(
        name="a",
    )

    b = FieldSpec(
        name="b",
    )

    a.derived_from.append(
        "base.field"
    )

    assert (
        b.derived_from == []
    )
