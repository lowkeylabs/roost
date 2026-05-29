# src/owlroost/audit/catalog.py

from __future__ import annotations

from collections import Counter

from owlroost.catalog.service import (
    load_catalog,
)


def audit_catalog() -> int:
    print("CATALOG")
    print("-------")

    failures = 0

    catalog = load_catalog()

    counts = Counter(
        spec.field_name
        for spec in catalog.values()
    )

    duplicates = [
        k
        for k, v in counts.items()
        if v > 1
    ]

    for name in duplicates:
        failures += 1

        print(
            f"duplicate semantic "
            f"identity: {name}"
        )

    print()

    return failures
