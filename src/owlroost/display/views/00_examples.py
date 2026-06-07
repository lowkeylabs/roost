# src/owlroost/display/views/00_examples.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Display view examples.

Notes
-----
Architectural examples for DisplayView.

All example views live within the
example-* namespace.

Example views may reference only:

    example.*

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
    # Single-group view
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="example-scalar",
            description=("Minimal example view."),
            entries=[
                (
                    "group",
                    "example.scalar",
                ),
            ],
        )
    )

    # =====================================================
    # Overlay examples
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="example-overlays",
            description=("Schema and metric overlay examples."),
            entries=[
                (
                    "group",
                    "example.overlays",
                ),
            ],
        )
    )

    # =====================================================
    # Synthetic examples
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="example-synthetic",
            description=("Synthetic field examples."),
            entries=[
                (
                    "group",
                    "example.synthetic",
                ),
            ],
        )
    )

    # =====================================================
    # Profile examples
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="example-profiles",
            description=("Profile-related examples."),
            entries=[
                (
                    "group",
                    "example.profiles",
                ),
            ],
        )
    )

    # =====================================================
    # Nested expansion
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="example-summary",
            description=("Exercises nested group expansion."),
            entries=[
                (
                    "group",
                    "example.summary",
                ),
            ],
        )
    )

    # =====================================================
    # Full architecture view
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="example-architecture",
            description=(
                "Exercises overlays, synthetics, profiles, groups, and recursive expansion."
            ),
            entries=[
                (
                    "group",
                    "example.architecture",
                ),
            ],
        )
    )

    # =====================================================
    # Catalog-level example
    # =====================================================

    reg.register_view(
        DisplayView(
            level="catalog",
            name="example-catalog",
            description=("Catalog-oriented example."),
            entries=[
                (
                    "group",
                    "example.architecture",
                ),
            ],
        )
    )
