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
from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)

# =========================================================
# Methodology Ontology
# =========================================================

BALANCE_SHEET_ONTOLOGY = dict(
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

    reg.register_display_field(
        DisplayField.field(
            "balance_sheet.fixed_assets_debt_remaining_value",
            profiles={
                "table": DisplayProfile(
                    label="Fixed\nAssets\nDebt\nRemain",
                    width=7,
                    fmt="currency_short",
                    content_align="right",
                    label_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Fixed assets debt remaining",
                    fmt="currency",
                ),
            },
            **BALANCE_SHEET_ONTOLOGY,
        )
    )
