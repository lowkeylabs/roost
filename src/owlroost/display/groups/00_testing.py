# src/owlroost/display/groups/00_testing.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
Display group testing fixtures.

Notes
-----
Deterministic groups intended for
automated testing.

All groups live within the:

    testing.*

namespace.

Testing groups may reference only:

    testing.*

fields and groups.
"""

from __future__ import annotations

from owlroost.display.specs import (
    DisplayGroup,
)


def register_display_groups(
    reg,
):
    # =====================================================
    # Basic field group
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="testing.basic",
            description=("Basic testing group."),
            entries=[
                "testing.scalar",
                "testing.string",
            ],
        )
    )

    # =====================================================
    # Boolean group
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="testing.boolean",
            description=("Boolean testing group."),
            entries=[
                "testing.boolean",
            ],
        )
    )

    # =====================================================
    # Composed group
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="testing.composed",
            description=("Composed testing group."),
            entries=[
                "testing.composed",
                "testing.semantic",
            ],
        )
    )

    # =====================================================
    # Nested group
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="testing.summary",
            description=("Nested testing group."),
            entries=[
                (
                    "group",
                    "testing.basic",
                ),
                (
                    "group",
                    "testing.boolean",
                ),
                (
                    "group",
                    "testing.composed",
                ),
            ],
        )
    )

    # =====================================================
    # Expansion stress test
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="testing.expansion",
            description=("Exercises recursive group expansion."),
            entries=[
                (
                    "group",
                    "testing.summary",
                ),
            ],
        )
    )
