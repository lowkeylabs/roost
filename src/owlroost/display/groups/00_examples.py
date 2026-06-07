# src/owlroost/display/groups/00_examples.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Display group examples.

Notes
-----
Architectural examples for DisplayGroup.

All groups live within the:

    example.*

namespace.

Example groups may reference only:

    example.*

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
    # Single-field group
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="example.scalar",
            description=("Single example field."),
            entries=[
                "example.synthetic",
            ],
        )
    )

    # =====================================================
    # Overlay examples
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="example.overlays",
            description=("Schema and metric overlay examples."),
            entries=[
                "example.bequest_overlay",
                "example.runtime_metric",
            ],
        )
    )

    # =====================================================
    # Synthetic examples
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="example.synthetic",
            description=("Synthetic field examples."),
            entries=[
                "example.synthetic",
                "example.composed",
                "example.semantic",
            ],
        )
    )

    # =====================================================
    # Profile examples
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="example.profiles",
            description=("Profile examples."),
            entries=[
                "example.multiple_profiles",
                "example.hidden",
            ],
        )
    )

    # =====================================================
    # Nested group
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="example.summary",
            description=("Summary example."),
            entries=[
                (
                    "group",
                    "example.overlays",
                ),
                (
                    "group",
                    "example.synthetic",
                ),
            ],
        )
    )

    # =====================================================
    # Full architecture example
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="example.architecture",
            description=("Exercises most group expansion patterns."),
            entries=[
                (
                    "group",
                    "example.summary",
                ),
                (
                    "group",
                    "example.profiles",
                ),
            ],
        )
    )
