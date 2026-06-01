# src/owlroost/display/sync.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

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


def path_to_table_label(
    field_name: str,
) -> str:
    """
    Generate compact table-oriented label.
    """

    # -----------------------------------------------------
    # Aggregate fields
    # -----------------------------------------------------

    if "__" in field_name:
        (
            base,
            agg,
        ) = field_name.rsplit(
            "__",
            1,
        )

        leaf = base.split(".")[-1]

        return f"{leaf.replace('_', ' ').title()} {agg.upper()}"

    # -----------------------------------------------------
    # Standard fields
    # -----------------------------------------------------

    leaf = field_name.split(".")[-1]

    return leaf.replace(
        "_",
        "\n",
    ).title()


def path_to_pivot_label(
    field_name: str,
) -> str:
    """
    Generate descriptive pivot-oriented label.
    """

    # -----------------------------------------------------
    # Aggregate fields
    # -----------------------------------------------------

    if "__" in field_name:
        (
            base,
            agg,
        ) = field_name.rsplit(
            "__",
            1,
        )

        return f"{base.replace('.', ' ').replace('_', ' ').title()} {agg.upper()}"

    # -----------------------------------------------------
    # Standard fields
    # -----------------------------------------------------

    if "." in field_name:
        field_name = field_name.split(
            ".",
            1,
        )[1]

    return field_name.replace(
        "_",
        " ",
    ).title()


# =========================================================
# Internal Overlay Registration
# =========================================================


def _register_field_if_missing(
    *,
    field_name: str,
    description: str | None,
    display_registry: DisplayRegistry,
    ontology_field=None,
    profiles=None,
):
    """
    Register DisplayField overlay if missing.

    Notes
    -----
    Display fields are presentation overlays
    layered atop canonical ontology.

    Existing explicit registrations are
    preserved.
    """

    # -----------------------------------------------------
    # Preserve explicit registrations
    # -----------------------------------------------------

    if display_registry.has_display_field(field_name):
        return

    # -----------------------------------------------------
    # Default Profiles
    # -----------------------------------------------------

    if profiles is None:
        profiles = {
            "table": DisplayProfile(
                label=path_to_table_label(field_name),
            ),
            "pivot": DisplayProfile(
                label=path_to_pivot_label(field_name),
            ),
        }

    # -----------------------------------------------------
    # Overlay Registration
    # -----------------------------------------------------

    display_registry.register_display_field(
        DisplayField(
            field_name=field_name,
            description=description,
            ontology_field=ontology_field,
            profiles=profiles,
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
    Generate DisplayField overlays from
    canonical schema ontology.
    """

    for schema_field in schema_registry.all():
        _register_field_if_missing(
            field_name=schema_field.name,
            description=(schema_field.description),
            display_registry=(display_registry),
            ontology_field=schema_field,
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
    Generate DisplayField overlays from
    canonical metrics ontology.
    """

    for metrics_field in metrics_registry.all():
        _register_field_if_missing(
            field_name=metrics_field.name,
            description=getattr(
                metrics_field,
                "description",
                None,
            ),
            ontology_field=metrics_field,
            display_registry=(display_registry),
            profiles=getattr(
                metrics_field,
                "profiles",
                None,
            ),
        )
