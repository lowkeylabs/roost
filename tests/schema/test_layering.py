from __future__ import annotations

from owlroost.schema.specs import (
    FieldSpec,
)


# =========================================================
# Canonical Projection Semantics
# =========================================================


def test_schema_fields_default_to_canonical():

    f = FieldSpec(
        name="solver_options.bequest",
    )

    assert (
        f.projection_kind
        == "canonical"
    )


# =========================================================
# Executable Ontology Semantics
# =========================================================


def test_schema_field_materialization_level():

    f = FieldSpec(
        name="solver_options.bequest",
        materialization_level="run",
    )

    assert (
        f.materialization_level
        == "run"
    )


def test_schema_field_runtime_source():

    f = FieldSpec(
        name="solver_options.bequest",
        source="input",
    )

    assert (
        f.source
        == "input"
    )


# =========================================================
# Name / Path Consistency
# =========================================================


def test_field_name_matches_path():

    f = FieldSpec(
        name="solver_options.bequest",
        path=(
            "solver_options",
            "bequest",
        ),
    )

    assert (
        ".".join(f.path)
        == f.name
    )


# =========================================================
# Ontology Stability
# =========================================================


def test_schema_field_owner_stable():

    f = FieldSpec(
        name="solver_options.bequest",
        owner="OWL",
    )

    assert f.owner == "OWL"


def test_schema_field_semantic_domain_stable():

    f = FieldSpec(
        name="solver_options.bequest",
        semantic_domain="decision",
    )

    assert (
        f.semantic_domain
        == "decision"
    )


def test_schema_field_value_origin_stable():

    f = FieldSpec(
        name="solver_options.bequest",
        value_origin="user-specified",
    )

    assert (
        f.value_origin
        == "user-specified"
    )
