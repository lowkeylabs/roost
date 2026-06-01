# tests/display/test_specs.py

from __future__ import annotations

from owlroost.display.specs import (
    DisplayField,
)

# =========================================================
# Basic Construction
# =========================================================


def test_field_constructor():
    """
    Preferred constructor should preserve
    field identity.
    """

    field = DisplayField.field(
        "solver_options.bequest",
    )

    assert field.field_name == "solver_options.bequest"


def test_non_synthetic_field_defaults():
    """
    Ordinary ontology-backed fields should
    not automatically become synthetic.
    """

    field = DisplayField.field(
        "solver_options.bequest",
    )

    assert not field.is_synthetic

    assert field.owner is None

    assert field.semantic_domain is None

    assert field.value_origin is None

    assert field.derived_from == []


# =========================================================
# Synthetic Classification
# =========================================================


def test_display_fn_implies_synthetic():
    """
    Synthetic classification should be
    inferred from display_fn.
    """

    def compute(row):
        return 123

    field = DisplayField.field(
        "display.net_worth",
        display_fn=compute,
    )

    assert field.is_synthetic


def test_lineage_implies_synthetic():
    """
    Synthetic classification should be
    inferred from derived_from.
    """

    field = DisplayField.field(
        "display.net_worth",
        derived_from=[
            "display.total_savings",
        ],
    )

    assert field.is_synthetic


def test_projection_kind_implies_synthetic():
    """
    Synthetic classification should be
    inferred from ontology metadata.
    """

    field = DisplayField.field(
        "display.net_worth",
        projection_kind="synthetic",
    )

    assert field.is_synthetic


# =========================================================
# Synthetic Defaults
# =========================================================


def test_synthetic_defaults_populated():
    """
    Synthetic fields should automatically
    receive default ontology metadata.
    """

    field = DisplayField.field(
        "display.net_worth",
        derived_from=[
            "display.total_savings",
        ],
    )

    assert field.is_synthetic

    assert field.owner == "ROOST"

    assert field.semantic_domain == "decision"

    assert field.value_origin == "roost-computed"

    assert field.projection_kind == "synthetic"

    assert field.analytic_kind == "synthetic"

    assert field.materialization_level == "case"


def test_explicit_ontology_preserved():
    """
    Explicit ontology metadata should
    override defaults.
    """

    field = DisplayField.field(
        "display.net_worth",
        derived_from=[
            "display.total_savings",
        ],
        owner="OWL",
        semantic_domain="execution",
        value_origin="user-specified",
    )

    assert field.owner == "OWL"

    assert field.semantic_domain == "execution"

    assert field.value_origin == "user-specified"


# =========================================================
# Lineage
# =========================================================


def test_preserves_dependencies():
    """
    Derived lineage should be preserved.
    """

    field = DisplayField.field(
        "display.net_worth",
        derived_from=[
            "display.total_savings",
            "display.net_hfp_assets",
        ],
    )

    assert field.derived_from == [
        "display.total_savings",
        "display.net_hfp_assets",
    ]


def test_default_dependencies_empty():
    """
    Lineage should default to empty.
    """

    field = DisplayField.field(
        "solver_options.bequest",
    )

    assert field.derived_from == []


# =========================================================
# Metadata
# =========================================================


def test_preserves_description():
    """
    Description metadata should survive
    construction.
    """

    field = DisplayField.field(
        "display.net_worth",
        description="Household net worth.",
    )

    assert field.description == "Household net worth."


def test_preserves_display_fn():
    """
    Computation callback should survive
    construction.
    """

    def compute(row):
        return 123

    field = DisplayField.field(
        "display.net_worth",
        display_fn=compute,
    )

    assert field.display_fn is compute


# =========================================================
# Path Handling
# =========================================================


def test_default_path_is_field_name():
    """
    Path should default to field_name.
    """

    field = DisplayField.field(
        "solver_options.bequest",
    )

    assert field.path == "solver_options.bequest"


def test_explicit_path_preserved():
    """
    Explicit paths should not be modified.
    """

    field = DisplayField.field(
        "display.net_worth",
        path="results.net_worth",
    )

    assert field.path == "results.net_worth"


# =========================================================
# Profiles
# =========================================================


def test_profiles_default_empty():
    """
    Profiles should default to empty.
    """

    field = DisplayField.field(
        "solver_options.bequest",
    )

    assert field.profiles == {}


# =========================================================
# Architectural Invariants
# =========================================================


def test_synthetic_and_non_synthetic_distinction():
    """
    Classification should emerge from
    ontology and lineage metadata.
    """

    ordinary = DisplayField.field(
        "solver_options.bequest",
    )

    synthetic = DisplayField.field(
        "display.net_worth",
        derived_from=[
            "display.total_savings",
        ],
    )

    assert not ordinary.is_synthetic

    assert synthetic.is_synthetic
