# src/owlroost/display/fields/catalog.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

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

from owlroost.core.utils import normalize_module_path
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
    defined_in=normalize_module_path(__file__),
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

    reg.register_display_field(
        DisplayField.field(
            "expands_to",
            description=(
                "Variables generated when this entity expands into multiple semantic variables."
            ),
            profiles={
                "table": DisplayProfile(
                    label="Expands To",
                    width=20,
                    wrap=True,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "defined_in",
            description="Module where the field is defined.",
            display_fn=debug_defined_in,
            profiles={
                "table": DisplayProfile(
                    label="Defined In",
                    width=20,
                    wrap=True,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "origin_file",
            description="Module where the variable was originally registered.",
            display_fn=lambda row: (
                row.get("_catalog", {}).get("provenance_chain", [{}])[0].get("file")
                if row.get("_catalog", {}).get("provenance_chain")
                else None
            ),
            profiles={
                "table": DisplayProfile(
                    label="Origin File",
                    width=25,
                    wrap=True,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "provenance_depth",
            description="Number of provenance events.",
            display_fn=lambda row: len(row.get("_catalog", {}).get("provenance_chain", [])),
            profiles={
                "table": DisplayProfile(
                    label="Prov Depth",
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "overlay_layers",
            description="Catalog layers contributing to this variable.",
            display_fn=lambda row: ", ".join(row.get("_catalog", {}).get("overlay_layers", [])),
            profiles={
                "table": DisplayProfile(
                    label="Layers",
                    width=20,
                    wrap=True,
                ),
            },
            **CATALOG_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "provenance_summary",
            description="Compact provenance summary.",
            display_fn=provenance_summary_display,
            profiles={
                "table": DisplayProfile(
                    label="Prov Summary",
                    width=40,
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
            display_fn=profiles_display,
            profiles={
                "table": DisplayProfile(
                    label="Defined Profiles",
                    width=30,
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
            display_fn=provenance_chain_display,
            profiles={
                "table": DisplayProfile(
                    label="Provenance Chain",
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


def debug_defined_in(row):
    chain = row.get("_catalog", {}).get("provenance_chain", [])

    if not chain:
        return None

    return chain[-1]["file"]


def provenance_chain_display(
    row,
):
    chain = row.get("_catalog", {}).get("provenance_chain", [])

    if not chain:
        return None

    return "\n".join(
        (f"{event.get('stage')}:{event.get('operation').value}\n  {event.get('file')}")
        for event in chain
    )


def provenance_summary_display(
    row,
):
    """
    Compact provenance summary.
    """

    chain = row.get("_catalog", {}).get("provenance_chain", [])

    if not chain:
        return None

    return " → ".join(
        event.get(
            "stage",
            "?",
        )
        for event in chain
    )


def profiles_display(
    row,
):
    details = row.get(
        "_display",
        {},
    ).get(
        "profile_details",
        {},
    )

    if not details:
        return None

    lines = []

    for name, profile in sorted(
        details.items(),
    ):
        label = str(
            profile.get(
                "label",
                "",
            )
        ).replace(
            "\n",
            "\\n",
        )

        lines.append(
            f"{name}: {{ label='{label}', fmt={profile.get('fmt')}, width={profile.get('width')} }}"
        )

    return "\n".join(
        lines,
    )
