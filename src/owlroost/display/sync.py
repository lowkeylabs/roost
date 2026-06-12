# src/owlroost/display/sync.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Display overlay synchronization.

Notes
-----
Synchronizes canonical schema and metric
registries into renderer-facing display
overlays.

Responsibilities
----------------
This module generates default DisplayField
instances for variables discovered in:

    - SchemaRegistry
    - MetricsRegistry

These generated overlays provide:

    - labels
    - formatting profiles
    - visibility defaults

without duplicating ontology metadata.

Architectural Invariant
-----------------------
Display owns presentation.

Catalog owns semantic identity.

SchemaRegistry and MetricsRegistry own
canonical ontology.

Therefore this module generates only
presentation overlays and must not attach
ontology objects to DisplayField instances.
"""

from __future__ import annotations

from owlroost.core.utils import normalize_module_path
from owlroost.display.registry import (
    DisplayRegistry,
)
from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)

# =========================================================
# Label Helpers
# =========================================================


def _display_parts(
    field_name: str,
):
    """
    Convert a field path into display parts.
    """

    agg = None

    if "__" in field_name:
        field_name, agg = field_name.rsplit(
            "__",
            1,
        )

    path_parts = field_name.split(".")

    # drop namespace
    if len(path_parts) > 1:
        path_parts = path_parts[1:]

    parts = []

    for part in path_parts:
        parts.extend(piece.title() for piece in part.split("_"))

    if agg is not None:
        parts.append(
            agg.lower(),
        )

    return parts


def path_to_table_label(
    field_name: str,
) -> str:
    """
    Generate compact table-oriented label.
    """

    return "\n".join(
        _display_parts(
            field_name,
        )
    )


def path_to_pivot_label(
    field_name: str,
) -> str:
    """
    Generate descriptive pivot-oriented label.
    """

    return " ".join(
        _display_parts(
            field_name,
        )
    )


# =========================================================
# Internal Overlay Registration
# =========================================================


def _register_field_if_missing(
    *,
    field_name: str,
    description: str | None,
    display_registry: DisplayRegistry,
    profiles=None,
):
    """
    Register default display overlay.

    Notes
    -----
    Explicitly registered display fields
    always take precedence.

    This helper creates only presentation
    overlays and intentionally does not
    copy ontology metadata from schema
    or metrics registries.
    """

    # -----------------------------------------------------
    # Preserve Explicit Registrations
    # -----------------------------------------------------

    if display_registry.has_display_field(
        field_name,
    ):
        return

    # -----------------------------------------------------
    # Default Formatting
    # -----------------------------------------------------

    table_fmt = None
    pivot_fmt = None
    table_content_align = None
    pivot_content_align = None

    if field_name.startswith(
        (
            "financial.",
            "balance_sheet.",
        )
    ):
        table_fmt = "currency_short"
        pivot_fmt = "currency"
        table_content_align = "right"
        pivot_content_align = "left"

        if field_name == "balance_sheet.has_hfp_file":
            table_fmt = "boolean_flag"

    # -----------------------------------------------------
    # Default Profiles
    # -----------------------------------------------------

    if not profiles:
        profiles = {
            "table": DisplayProfile(
                label=path_to_table_label(
                    field_name,
                ),
                fmt=table_fmt,
                content_align=table_content_align,
            ),
            "pivot": DisplayProfile(
                label=path_to_pivot_label(
                    field_name,
                ),
                fmt=pivot_fmt,
                content_align=pivot_content_align,
            ),
        }

    # -----------------------------------------------------
    # Register Overlay
    # -----------------------------------------------------

    display_registry.register_display_field(
        DisplayField(
            field_name=field_name,
            description=description,
            profiles=profiles,
            defined_in=normalize_module_path(__file__),
        )
    )


# =========================================================
# Schema Overlay Sync
# =========================================================


def sync_schema_registry(
    schema_registry,
    display_registry: DisplayRegistry,
):
    """
    Generate default display overlays for
    schema variables.
    """

    for schema_field in schema_registry.all():
        _register_field_if_missing(
            field_name=schema_field.name,
            description=(schema_field.description),
            display_registry=(display_registry),
            profiles=getattr(
                schema_field,
                "profiles",
                None,
            ),
        )


# =========================================================
# Metrics Overlay Sync
# =========================================================


def sync_metrics_registry(
    metrics_registry,
    display_registry: DisplayRegistry,
):
    """
    Generate default display overlays for
    metric variables.
    """

    for metrics_field in metrics_registry.all():
        _register_field_if_missing(
            field_name=metrics_field.name,
            description=getattr(
                metrics_field,
                "description",
                None,
            ),
            display_registry=(display_registry),
            profiles=getattr(
                metrics_field,
                "profiles",
                None,
            ),
        )
