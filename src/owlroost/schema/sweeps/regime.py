# src/owlroost/schema/sweeps/regime.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
rates_selection.regime sweep variable.
"""

from __future__ import annotations

from owlroost.catalog.ontology import (
    CatalogNodeType,
)

from ..registry import (
    FieldSpec,
)

MARKET_REGIMES = {
    "full": (1928, 2025),
    "dotcom": (1994, 2000),
    "stagflation": (1966, 1982),
}


def register_schema_fields(
    reg,
):
    reg.register(
        FieldSpec(
            name="roost_sweeps.regime",
            dtype=str,
            path=(
                "roost_sweeps",
                "regime",
            ),
            source="sweep",
            owner="ROOST",
            semantic_domain="decision",
            value_origin="user-specified",
            projection_kind="canonical",
            analytic_kind="observed",
            materialization_level="run",
            node_type=CatalogNodeType.VARIABLE,
            expands_to=[
                "rates_selection.from",
                "rates_selection.to",
            ],
            description=("Named historical market regime."),
            defined_in="regime",
        )
    )


def expand(
    run_dict,
):
    roost = run_dict.setdefault(
        "roost_sweeps",
        {},
    )

    regime = roost.pop(
        "regime",
        None,
    )

    rates = run_dict.setdefault(
        "rates_selection",
        {},
    )

    if not regime:
        return

    if regime not in MARKET_REGIMES:
        raise ValueError(f"Unknown regime: {regime}")

    start, end = MARKET_REGIMES[regime]

    rates["from"] = start
    rates["to"] = end
