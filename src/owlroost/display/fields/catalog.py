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

    These fields are used by:

        roost vars
    """

    reg.register_display_field(
        DisplayField(
            field_name="field_name",
            description="Catalog variable name",
            profiles={
                "table": DisplayProfile(
                    label="Variable",
                    width=40,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="layer",
            description="Ontology ownership layer",
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
            field_name="source",
            description="Runtime provenance source",
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
            description="Underlying storage path",
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
            field_name="description",
            description="Semantic description",
            profiles={
                "table": DisplayProfile(
                    label="Description",
                    width=60,
                    wrap=True,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="semantic_owner",
            description="Semantic ontology owner",
            profiles={
                "table": DisplayProfile(
                    label="Owner",
                    width=16,
                ),
            },
        )
    )
