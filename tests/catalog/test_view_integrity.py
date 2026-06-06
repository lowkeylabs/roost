from __future__ import annotations

from owlroost.display.materializers.materialize import (
    expand_view_entries,
)


def test_all_view_fields_exist(
    registries,
):
    """
    Every field referenced by every view
    must have a registered DisplayField.
    """

    (
        schema_registry,
        metrics_registry,
        display_registry,
    ) = registries

    for view in display_registry.all_views():
        entries = expand_view_entries(
            display_registry,
            view.entries,
        )

        for entry in entries:
            if entry.get("kind") == "section":
                continue

            display_registry.get_display_field(
                entry["field"],
            )
