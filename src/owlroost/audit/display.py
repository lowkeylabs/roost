# src/owlroost/audit/display.py

from __future__ import annotations

from owlroost.display.bootstrap import (
    build_display_registry,
)
from owlroost.metrics.registry import (
    build_metrics_registry,
)
from owlroost.schema.registry import (
    build_registry,
)


def audit_display() -> int:
    print("DISPLAY")
    print("-------")

    failures = 0

    schema_registry = build_registry()

    metrics_registry = (
        build_metrics_registry()
    )

    display_registry = (
        build_display_registry(
            schema_registry,
            metrics_registry,
        )
    )

    for field in (
        display_registry.fields.values()
    ):
        if (
            field.ontology_field
            is None
            and field.field_name
            not in {
                "compact_id",
                "compact_threads",
            }
        ):
            print(
                f"{field.field_name}: "
                f"missing ontology link"
            )

    print()

    return failures
