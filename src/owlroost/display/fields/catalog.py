# src/owlroost/display/fields/catalog.py

"""
Catalog display fields.

Notes
-----
Presentation overlays for canonical
catalog rows.

These fields expose catalog metadata
through the normal display/materialization
pipeline so catalog rows participate in
views exactly like any other row source.
"""

from __future__ import annotations

from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)

# =========================================================
# Catalog Ontology
# =========================================================

CATALOG_ONTOLOGY = dict(
    owner="ROOST",
    semantic_domain="design",
    value_origin="roost-computed",
    projection_kind="synthetic",
    analytic_kind="observed",
    materialization_level="catalog",
    node_type="variable",
)


# =========================================================
# Registration
# =========================================================


def register_display_fields(
    reg,
):
    """
    Register catalog display fields.
    """

    # =====================================================
    # Identity
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "field_name",
            description="Canonical semantic variable name.",
            profiles={
                "table": DisplayProfile(
                    label="Field",
                    width=40,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "path",
            description="Hierarchical variable path.",
            profiles={
                "table": DisplayProfile(
                    label="Path",
                    width=50,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "description",
            description="Semantic description.",
            profiles={
                "table": DisplayProfile(
                    label="Description",
                    width=60,
                    wrap=True,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    # =====================================================
    # Ownership
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "owner",
            description="Semantic owner.",
            profiles={
                "table": DisplayProfile(
                    label="Owner",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "layer",
            description="Catalog source layer.",
            profiles={
                "table": DisplayProfile(
                    label="Layer",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    # =====================================================
    # Ontology
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "semantic_domain",
            description="Semantic domain classification.",
            profiles={
                "table": DisplayProfile(
                    label="Domain",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "value_origin",
            description="Origin of the value.",
            profiles={
                "table": DisplayProfile(
                    label="Origin",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "projection_kind",
            description="Projection classification.",
            profiles={
                "table": DisplayProfile(
                    label="Projection",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "analytic_kind",
            description="Analytical interpretation.",
            profiles={
                "table": DisplayProfile(
                    label="Analytic",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "materialization_level",
            description="Materialization level.",
            profiles={
                "table": DisplayProfile(
                    label="Level",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "node_type",
            description="Catalog node classification.",
            profiles={
                "table": DisplayProfile(
                    label="Type",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    # =====================================================
    # Provenance
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "derived_from",
            description="Semantic lineage and provenance.",
            profiles={
                "table": DisplayProfile(
                    label="Derived From",
                    width=20,
                    wrap=True,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    # =====================================================
    # Diagnostics
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "display_name",
            description="Display-facing variable name.",
            profiles={
                "table": DisplayProfile(
                    label="Display Name",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "is_synthetic",
            description="Synthetic semantic variable flag.",
            profiles={
                "table": DisplayProfile(
                    label="Synthetic",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    # =====================================================
    # Catalog Metadata
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "source",
            description=("Source registry or originating catalog subsystem."),
            profiles={
                "table": DisplayProfile(
                    label="Source",
                    width=20,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "profiles",
            description=("Registered display profile names."),
            profiles={
                "table": DisplayProfile(
                    label="Profiles",
                    width=20,
                    wrap=True,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "provenance_chain",
            description=("Complete provenance evolution history."),
            profiles={
                "table": DisplayProfile(
                    label="Provenance",
                    width=40,
                    wrap=True,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    # =====================================================
    # Runtime Diagnostics
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "catalog_id",
            description=("Canonical catalog identifier."),
            profiles={
                "table": DisplayProfile(
                    label="Catalog ID",
                    width=20,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "profile_count",
            description=("Number of registered display profiles."),
            profiles={
                "table": DisplayProfile(
                    label="Profile Count",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )
