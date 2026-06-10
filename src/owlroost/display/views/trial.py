# src/owlroost/display/views/trial.py
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
            level="trial",
            name="trial",
            entries=[
                "case_name",
                "display.compact_id",
                "display.optimization_goal",
                "display.completion_fraction",
                "financial.spending.year0.today",
                "financial.spending.total.today",
                "financial.bequest.total.today",
            ],
            description=(""),
        )
    )
