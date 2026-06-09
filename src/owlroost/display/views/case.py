# src/owlroost/display/views/case.py
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
            level="case",
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
            level="case",
            name="cases",
            entries=[
                # =====================================
                # Identity
                # =====================================
                "case_name",
                ("description", {"modes": ["pivot"]}),
                "basic_info.names",
                "display.starting_ages",
                "basic_info.life_expectancy",
                "balance_sheet.net_worth",
            ],
            description=(""),
        )
    )

    reg.register_view(
        DisplayView(
            level="case",
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
            level="case",
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
                "balance_sheet.fixed_assets",
                ("section", "Liability Detail"),
                "balance_sheet.mortgage_debt",
            ],
            description=(
                "Summarizes household financial position "
                "including retirement savings, fixed "
                "assets, liabilities, total assets, "
                "and net worth."
            ),
        )
    )
