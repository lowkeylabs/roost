# src/owlroost/catalog/rows.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
Catalog row materialization.

Notes
-----
Transforms canonical catalog specifications
into lightweight runtime rows suitable for:

    - filtering
    - sorting
    - rendering
    - explainability
    - CLI inspection

Architectural Invariant
-----------------------

Catalog rows are the canonical runtime
representation of semantic entities.

Catalog rows intentionally contain all
metadata required for inspection and
rendering.

Authoring objects are not retained.
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    is_dataclass,
)

from owlroost.catalog.provenance import (
    defined_in,
    origin_file,
    provenance_depth,
)
from owlroost.catalog.specs import (
    CatalogSpec,
    ProvenanceEvent,
)

# =========================================================
# Provenance Export
# =========================================================


def _export_provenance_chain(
    chain: list[ProvenanceEvent],
):
    """
    Export provenance chain into stable,
    renderer-safe structures.
    """

    rows = []

    for event in chain:
        if is_dataclass(event):
            rows.append(asdict(event))
        else:
            rows.append(
                {
                    "type": str(
                        type(event).__name__,
                    )
                }
            )

    return rows


# =========================================================
# Catalog Row Builder
# =========================================================


def build_catalog_row(
    *,
    spec: CatalogSpec,
    layer: str,
    semantic_field=None,
    display_field=None,
):
    """
    Construct canonical catalog row.
    """

    # =====================================================
    # Provenance
    # =====================================================

    provenance_chain = _export_provenance_chain(
        spec.provenance_chain,
    )

    origin = origin_file(
        spec.provenance_chain,
    )

    defined = defined_in(
        spec.provenance_chain,
    )

    prov_depth = provenance_depth(
        spec.provenance_chain,
    )

    # =====================================================
    # Display Metadata
    # =====================================================

    display_name = None
    profiles = []
    profile_details = {}

    if display_field is not None:
        profiles = sorted(
            display_field.profiles.keys(),
        )

        profile_details = {
            name: {
                "label": profile.label,
                "fmt": profile.fmt,
                "width": profile.width,
                "label_align": profile.label_align,
                "content_align": profile.content_align,
                "wrap": profile.wrap,
                "visible": profile.visible,
            }
            for name, profile in display_field.profiles.items()
        }

        table_profile = display_field.profiles.get(
            "table",
        )

        if table_profile is not None:
            display_name = table_profile.label

    # =====================================================
    # Overlay Metadata
    # =====================================================

    overlay_layers: list[str] = []

    if layer == "display":
        overlay_layers.append(
            "display",
        )

    # =====================================================
    # Canonical Row
    # =====================================================

    row = {
        # -------------------------------------------------
        # Operational Metadata
        # -------------------------------------------------
        "_meta": {
            "layer": layer,
        },
        # -------------------------------------------------
        # Canonical Ontology
        # -------------------------------------------------
        "_catalog": {
            "field_name": spec.field_name,
            "owner": spec.owner,
            "semantic_domain": spec.semantic_domain,
            "value_origin": spec.value_origin,
            "projection_kind": spec.projection_kind,
            "analytic_kind": spec.analytic_kind,
            "materialization_level": spec.materialization_level,
            "node_type": spec.node_type,
            "source": spec.source,
            "path": spec.path,
            "derived_from": list(
                spec.derived_from,
            ),
            "provenance_chain": provenance_chain,
            "overlay_layers": overlay_layers,
            "origin_file": origin,
            "defined_in": defined,
        },
        # -------------------------------------------------
        # Display Metadata
        # -------------------------------------------------
        "_display": {
            "description": spec.description,
            "display_name": display_name,
            "profiles": profiles,
            "profile_details": profile_details,
        },
        # -------------------------------------------------
        # Flattened Convenience Aliases
        # -------------------------------------------------
        "field_name": spec.field_name,
        "layer": layer,
        "owner": spec.owner,
        "semantic_domain": spec.semantic_domain,
        "value_origin": spec.value_origin,
        "projection_kind": spec.projection_kind,
        "analytic_kind": spec.analytic_kind,
        "materialization_level": spec.materialization_level,
        "node_type": spec.node_type,
        "source": spec.source,
        "path": spec.path,
        "description": spec.description,
        "derived_from": list(
            spec.derived_from,
        ),
        "origin_file": origin,
        "defined_in": defined,
        "provenance_depth": prov_depth,
        "overlay_layers": list(
            overlay_layers,
        ),
        "display_name": display_name,
        "profiles": profiles,
    }

    return row
