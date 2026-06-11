# src/owlroost/display/fields/balance_sheet.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Balance sheet fields.

Notes
-----
xxx
"""

from __future__ import annotations

from owlroost.core.utils import normalize_module_path
from owlroost.display.operations.normalize import (
    get_units_multiplier,
)
from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)

# =========================================================
# Methodology Ontology
# =========================================================

BALANCE_SHEET_ONTOLOGY = dict(
    owner="ROOST",
    semantic_domain="decision",
    value_origin="roost-computed",
    projection_kind="synthetic",
    analytic_kind="synthetic",
    materialization_level="case",
    node_type="variable",
    defined_in=normalize_module_path(__file__),
)


def register_display_fields(
    reg,
):
    """
    Register methodology display fields.
    """

    # overrides with new display profiles
    reg.register_display_field(
        DisplayField.field(
            "savings_assets.taxable_savings_balances",
            profiles={
                "table": DisplayProfile(
                    label="Savings\nTaxable",
                    width=10,
                ),
                "pivot": DisplayProfile(
                    label="Taxable Savings",
                    width=16,
                ),
            },
            **BALANCE_SHEET_ONTOLOGY,
        )
    )


def compute_total_taxable_savings(
    row,
):
    """
    Sum taxable savings balances and
    return canonical dollars.
    """

    try:
        inputs = row.get(
            "_inputs",
            {},
        )

        multiplier = get_units_multiplier(
            inputs.get(
                "solver_options",
                {},
            ).get(
                "units",
                "k",
            )
        )

        values = inputs.get(
            "savings_assets",
            {},
        ).get(
            "taxable_savings_balances",
            [],
        )

        return sum(float(v or 0) * multiplier for v in values)

    except Exception:
        return None
