# src/owlroost/display/views/00_testing.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Display view testing fixtures.

Notes
-----
Deterministic views intended for
automated testing.

All testing views live within the
testing-* namespace.

Testing views may reference only:

    testing.*

groups.
"""

from __future__ import annotations

from owlroost.display.specs import (
    DisplayView,
)


def register_display_views(
    reg,
):
    # =====================================================
    # Basic fixture
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="testing-basic",
            description=("Basic deterministic view."),
            entries=[
                (
                    "group",
                    "testing.basic",
                ),
            ],
        )
    )

    # =====================================================
    # Boolean fixture
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="testing-boolean",
            description=("Boolean deterministic fixture."),
            entries=[
                (
                    "group",
                    "testing.boolean",
                ),
            ],
        )
    )

    # =====================================================
    # Composed fixture
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="testing-composed",
            description=("Composed deterministic fixture."),
            entries=[
                (
                    "group",
                    "testing.composed",
                ),
            ],
        )
    )

    # =====================================================
    # Nested fixture
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="testing-summary",
            description=("Nested deterministic fixture."),
            entries=[
                (
                    "group",
                    "testing.summary",
                ),
            ],
        )
    )

    # =====================================================
    # Recursive expansion fixture
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="testing-expansion",
            description=("Exercises recursive group expansion."),
            entries=[
                (
                    "group",
                    "testing.expansion",
                ),
            ],
        )
    )

    # =====================================================
    # Full testing fixture
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="testing-fixture",
            description=("Exercises the complete testing namespace."),
            entries=[
                (
                    "group",
                    "testing.expansion",
                ),
            ],
        )
    )
