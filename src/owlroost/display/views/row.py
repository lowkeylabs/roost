# src/owlroost/display/views/row.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.display.specs import (
    DisplayView,
)


def register_display_views(
    reg,
):
    """
    Register all display views.

    Views are declarative layouts composed
    from reusable display groups and fields.

    Views are uniquely identified by:

        (level, name)

    Examples:

        ("case", "basic")
        ("run", "results")
        ("session", "results")
    """

    reg.register_view(
        DisplayView(
            level="row",
            name="build",
            entries=[
                # =====================================
                # Identity
                # =====================================
                "case_name",
                ("description", {"modes": ["pivot"]}),
            ],
            description=(""),
        )
    )

    reg.register_view(
        DisplayView(
            level="row",
            name="cases",
            entries=[
                # =====================================
                # Identity
                # =====================================
                "case_name",
                ("description", {"modes": ["pivot"]}),
                ("basic_info.names", {"modes": ["pivot"]}),
                "display.starting_ages",
                "basic_info.life_expectancy",
                "balance_sheet.net_worth",
                "rates_selection.method",
                "display.optimization_goal",
            ],
            description=(""),
        )
    )

    reg.register_view(
        DisplayView(
            level="row",
            name="hfp",
            entries=[
                # =====================================
                # Identity
                # =====================================
                "case_name",
                ("description", {"modes": ["pivot"]}),
                "household_financial_profile.HFP_file_name",
                "balance_sheet.has_hfp_file",
                "balance_sheet.fixed_assets_current_value",
                "balance_sheet.fixed_assets_debt_remaining_value",
            ],
            description=(""),
        )
    )

    reg.register_view(
        DisplayView(
            level="row",
            name="descriptions",
            entries=[
                # =====================================
                # Identity
                # =====================================
                "case_name",
                "description",
            ],
            description=(""),
        )
    )

    reg.register_view(
        DisplayView(
            level="row",
            name="balance_sheet",
            entries=[
                # -------------------------------------------------
                # Summary
                # -------------------------------------------------
                ("case_name"),
                ("section", "Net Worth"),
                "balance_sheet.net_worth",
                ("section", "Assets and Liabilities"),
                "balance_sheet.total_assets",
                "balance_sheet.total_liabilities",
                # -------------------------------------------------
                # Asset Detail
                # -------------------------------------------------
                ("section", "Asset Details"),
                "balance_sheet.total_taxable_savings",
                "balance_sheet.total_tax_deferred_savings",
                "balance_sheet.total_tax_free_savings",
                "balance_sheet.fixed_assets_current_value",
                ("section", "Liability Detail"),
                "balance_sheet.fixed_assets_debt_remaining_value",
            ],
            description=(
                "Summarizes household financial position "
                "including retirement savings, fixed "
                "assets, liabilities, total assets, "
                "and net worth."
            ),
        )
    )
