# src/owlroost/audit/ontology.py

from __future__ import annotations

from owlroost.catalog.service import (
    load_catalog,
)


def audit_ontology() -> int:
    print("ONTOLOGY")
    print("--------")

    failures = 0

    catalog = load_catalog()

    for spec in catalog.values():

        if (
            spec.projection_kind
            == "aggregate"
            and spec.analytic_kind
            not in {
                "aggregate",
                "distributional",
            }
        ):
            failures += 1

            print(
                f"{spec.field_name}: "
                f"aggregate projection "
                f"missing aggregate "
                f"analytic_kind"
            )

    print()

    return failures
