# src/owlroost/display/sync.py

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

    Examples:

        runtime.trial_jobs
            -> Trial Jobs

        timing.elapsed_seconds
            -> Elapsed Seconds

        financial.bequest.total__median
            -> Total Median
    """

    # -----------------------------------------------------
    # Aggregate fields
    # -----------------------------------------------------

    if "__" in field_name:
        base, agg = field_name.rsplit(
            "__",
            1,
        )

        leaf = base.split(".")[-1]

        return f"{leaf.replace('_', ' ').title()} " f"{agg.upper()}"

    # -----------------------------------------------------
    # Standard fields
    # -----------------------------------------------------

    leaf = field_name.split(".")[-1]

    return leaf.replace(
        "_",
        " ",
    ).title()


def path_to_pivot_label(
    field_name: str,
) -> str:
    """
    Generate descriptive pivot-oriented label.

    Examples:

        runtime.trial_jobs
            -> Runtime Trial Jobs

        timing.elapsed_seconds
            -> Timing Elapsed Seconds

        financial.bequest.total__median
            -> Financial Bequest Total Median
    """

    # -----------------------------------------------------
    # Aggregate fields
    # -----------------------------------------------------

    if "__" in field_name:
        base, agg = field_name.rsplit(
            "__",
            1,
        )

        return f"{base.replace('.', ' ').replace('_', ' ').title()} " f"{agg.upper()}"

    # -----------------------------------------------------
    # Standard fields
    # -----------------------------------------------------

    return (
        field_name.replace(
            ".",
            " ",
        )
        .replace(
            "_",
            " ",
        )
        .title()
    )


# =========================================================
# Internal Helper
# =========================================================


def _register_field_if_missing(
    field_name: str,
    description: str | None,
    display_registry: DisplayRegistry,
    display_profiles=None,
):
    """
    Register DisplayField only if missing.

    Existing explicit overrides are preserved.
    """

    # -----------------------------------------------------
    # Preserve explicit registrations
    # -----------------------------------------------------

    if display_registry.has_display_field(field_name):
        return

    # -----------------------------------------------------
    # Auto-generated display field
    # -----------------------------------------------------

    display_field = DisplayField(
        field_name=field_name,
        description=description,
        profiles=(
            display_profiles
            or {
                "table": DisplayProfile(
                    label=path_to_table_label(field_name),
                ),
                "pivot": DisplayProfile(
                    label=path_to_pivot_label(field_name),
                ),
            }
        ),
    )

    display_registry.register_display_field(display_field)


# =========================================================
# Schema Sync
# =========================================================


def sync_schema_registry(
    schema_registry,
    display_registry: DisplayRegistry,
):
    """
    Auto-generate DisplayField objects
    from input SchemaRegistry fields.

    Existing DisplayFields are preserved.

    Only missing fields are created.

    The schema registry remains the
    authoritative INPUT semantic model.

    DisplayRegistry owns:
        - labels
        - formatting
        - alignment
        - visibility
        - grouping
        - views
    """

    for schema_field in schema_registry.all():
        _register_field_if_missing(
            field_name=schema_field.name,
            description=schema_field.description,
            display_registry=display_registry,
            display_profiles=getattr(
                schema_field,
                "display_profiles",
                None,
            ),
        )


# =========================================================
# Metrics Sync
# =========================================================


def sync_metrics_registry(
    metrics_registry,
    display_registry: DisplayRegistry,
):
    """
    Auto-generate DisplayField objects
    from MetricsRegistry fields.

    Metrics fields represent OUTPUT metrics,
    distinct from input configuration schema.

    Existing DisplayFields are preserved.

    MetricsRegistry remains the
    authoritative OUTPUT semantic model.
    """

    for metrics_field in metrics_registry.all():
        _register_field_if_missing(
            field_name=metrics_field.name,
            description=getattr(
                metrics_field,
                "description",
                None,
            ),
            display_registry=display_registry,
        )


# =========================================================
# Backward Compatibility Alias
# =========================================================

sync_display_registry = sync_schema_registry
