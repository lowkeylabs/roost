# tests/display/test_specs.py

from __future__ import annotations

from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
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

    assert field.field_name == ("solver_options.bequest")


def test_default_path_is_field_name():
    """
    Path should default to field_name.
    """

    field = DisplayField.field(
        "solver_options.bequest",
    )

    assert field.path == ("solver_options.bequest")


def test_explicit_path_preserved():
    """
    Explicit paths should not be modified.
    """

    field = DisplayField.field(
        "display.net_worth",
        path="results.net_worth",
    )

    assert field.path == ("results.net_worth")


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
        description=("Household net worth."),
    )

    assert field.description == ("Household net worth.")


def test_preserves_notes():
    """
    Notes metadata should survive
    construction.
    """

    field = DisplayField.field(
        "display.net_worth",
        notes="Example notes.",
    )

    assert field.notes == ("Example notes.")


def test_preserves_display_fn():
    """
    Display callback should survive
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
# Profiles
# =========================================================


def test_profiles_default_profile_created():
    """
    Fields without explicit profiles should
    receive a default profile automatically.
    """

    field = DisplayField.field(
        "solver_options.bequest",
    )

    assert "default" in field.profiles
    assert len(field.profiles) == 1


def test_preserves_profiles():
    """
    Profiles should survive
    construction.
    """

    profile = DisplayProfile(
        label="Example",
    )

    field = DisplayField.field(
        "display.net_worth",
        profiles={
            "table": profile,
        },
    )

    assert field.profiles == {
        "table": profile,
    }


# =========================================================
# Architectural Invariants
# =========================================================


def test_display_field_owns_presentation():
    """
    DisplayField should own renderer-facing
    metadata.
    """

    field = DisplayField.field(
        "display.net_worth",
        description="Net worth",
        notes="Example",
    )

    assert field.description == ("Net worth")

    assert field.notes == ("Example")


# =========================================================
# Catalog Declarations
# =========================================================


def test_lineage_requires_ontology():
    """
    Lineage metadata represents semantic
    lineage and therefore requires
    ontology metadata.
    """

    import pytest

    with pytest.raises(
        ValueError,
        match=("lineage metadata requires ontology metadata"),
    ):
        DisplayField.field(
            "example.overlay",
            derived_from=[
                "solver_options.bequest",
            ],
        )


def test_lineage_with_ontology_creates_catalog_declaration():
    """
    Semantic declarations carrying lineage
    should synthesize a CatalogSpec.
    """

    field = DisplayField.field(
        "example.overlay",
        owner="ROOST",
        semantic_domain="execution",
        value_origin="roost-computed",
        projection_kind="synthetic",
        derived_from=[
            "solver_options.bequest",
        ],
    )

    assert field.catalog_declaration is not None

    assert field.catalog_declaration.derived_from == [
        "solver_options.bequest",
    ]
