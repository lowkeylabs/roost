# src/owlroost/display/sync.py

from __future__ import annotations

from owlroost.display.registry import DisplayRegistry
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

        solver.elapsed_seconds
            -> Elapsed Seconds
    """

    leaf = field_name.split(".")[-1]

    return leaf.replace("_", " ").title()


def path_to_pivot_label(
    field_name: str,
) -> str:
    """
    Generate more descriptive pivot-oriented label.

    Examples:

        runtime.trial_jobs
            -> Runtime Trial Jobs

        solver.elapsed_seconds
            -> Solver Elapsed Seconds
    """

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
# Sync
# =========================================================


def sync_display_registry(
    schema_registry,
    display_registry: DisplayRegistry,
):
    """
    Auto-generate DisplayField objects
    from SchemaRegistry fields.

    Existing DisplayFields are preserved.

    Only missing fields are created.

    The schema registry remains the
    authoritative semantic model.

    The display registry owns
    presentation semantics.
    """

    for schema_field in schema_registry.all():
        field_name = schema_field.name

        # ----------------------------------------
        # Preserve explicit overrides
        # ----------------------------------------
        if display_registry.has_display_field(field_name):
            continue

        # ----------------------------------------
        # Build DisplayField
        # ----------------------------------------
        display_field = DisplayField(
            field_name=field_name,
            description=schema_field.description,
            profiles={
                "table": DisplayProfile(
                    label=path_to_table_label(field_name),
                ),
                "pivot": DisplayProfile(
                    label=path_to_pivot_label(field_name),
                ),
            },
        )

        display_registry.register_display_field(display_field)
