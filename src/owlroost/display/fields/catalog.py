# src/owlroost/display/fields/catalog.py

from __future__ import annotations

from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)


def register_display_fields(
    reg,
):
    """
    Register catalog display fields.

    These fields expose ontology metadata
    through the standard display subsystem.

    Used primarily by:

        roost vars
    """

    # =====================================================
    # Identity
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="field_name",
            description=("Canonical variable name."),
            profiles={
                "table": DisplayProfile(
                    label="Variable",
                    width=42,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="description",
            description=("Semantic variable description."),
            profiles={
                "table": DisplayProfile(
                    label="Description",
                    width=60,
                    wrap=True,
                ),
            },
        )
    )

    # =====================================================
    # Ontology Layer
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="layer",
            description=("Ontology registry layer."),
            profiles={
                "table": DisplayProfile(
                    label="Layer",
                    width=12,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="owner",
            description=("Semantic ontology owner."),
            profiles={
                "table": DisplayProfile(
                    label="Owner",
                    width=10,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="semantic_domain",
            description=("Scientific workflow role."),
            profiles={
                "table": DisplayProfile(
                    label="Domain",
                    width=12,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="value_origin",
            description=("Fundamental value origin."),
            profiles={
                "table": DisplayProfile(
                    label="Origin",
                    width=18,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="projection_kind",
            description=("Analytical projection type."),
            profiles={
                "table": DisplayProfile(
                    label="Projection",
                    width=14,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="materialization_level",
            description=("Runtime materialization level."),
            profiles={
                "table": DisplayProfile(
                    label="Level",
                    width=10,
                ),
            },
        )
    )

    # =====================================================
    # Runtime Provenance
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="source",
            description=("Runtime storage source."),
            profiles={
                "table": DisplayProfile(
                    label="Source",
                    width=16,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="path",
            description=("Underlying runtime storage path."),
            profiles={
                "table": DisplayProfile(
                    label="Path",
                    width=50,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="derived_from",
            description=("Lineage parent variable(s)."),
            profiles={
                "table": DisplayProfile(
                    label="Derived\nFrom",
                    width=28,
                    wrap=True,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="provenance_depth",
            description=("Number of provenance events."),
            profiles={
                "table": DisplayProfile(
                    label="Prov\nDepth",
                    width=8,
                    content_align="right",
                ),
            },
        )
    )
