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
                "basic_info.life_expectancy",
                "basic_info.date_of_birth",
            ],
            description=(""),
        )
    )
