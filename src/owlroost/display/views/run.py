# src/owlroost/display/views/run.py
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
            level="run",
            name="run",
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
            level="run",
            name="results",
            entries=[
                # =====================================
                # Identity
                # =====================================
                "case_name",
                "display.compact_id",
                "display.is_superseded",
                "display.superseded_by",
                "display.optimization_goal",
                "display.completion_fraction",
                "financial.spending.year0.today__median",
                "financial.spending.total.today__median",
                "financial.bequest.total.today__median",
                ("description", {"modes": ["pivot"]}),
            ],
            description=(""),
        )
    )

    reg.register_view(
        DisplayView(
            level="run",
            name="social_security",
            entries=[
                # =====================================
                # Identity
                # =====================================
                "case_name",
                "display.compact_id",
                "display.optimization_goal",
                "rates_selection.method",
                "display.completion_fraction",
                # "fixed_income.social_security_ages",
                # "solver_options.withSSAges",
                "social_security.optimized__constant",
                ("social_security.ages__median"),
                (
                    "financial.spending.total.today__median",
                    {"profiles": {"table": {"fmt": "currency"}}},
                ),
                "financial.bequest.total.today__median",
                ("description", {"modes": ["pivot"]}),
            ],
            description=(""),
        )
    )

    reg.register_view(
        DisplayView(
            level="run",
            name="social_security2",
            entries=[
                # =====================================
                # Identity
                # =====================================
                "case_name",
                "display.compact_id",
                # "display.optimization_goal",
                # "rates_selection.method",
                "display.completion_fraction",
                "fixed_income.social_security_ages",
                # "solver_options.withSSAges",
                # "social_security.optimized__constant",
                # ("social_security.ages__median"),
                (
                    "financial.spending.total.today__p10",
                    {"profiles": {"table": {"fmt": "currency"}}},
                ),
                (
                    "financial.spending.total.today__median",
                    {"profiles": {"table": {"fmt": "currency"}}},
                ),
                (
                    "financial.spending.total.today__p90",
                    {"profiles": {"table": {"fmt": "currency"}}},
                ),
                (
                    "financial.bequest.total.today__p10",
                    {"profiles": {"table": {"fmt": "currency"}}},
                ),
                (
                    "financial.bequest.total.today__median",
                    {"profiles": {"table": {"fmt": "currency"}}},
                ),
                (
                    "financial.bequest.total.today__p90",
                    {"profiles": {"table": {"fmt": "currency"}}},
                ),
            ],
            description=(""),
        )
    )
