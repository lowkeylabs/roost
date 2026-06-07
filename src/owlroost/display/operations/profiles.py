# src/owlroost/display/operations/profiles.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Display profile resolution.
"""

from __future__ import annotations

# =========================================================
# Profile Resolution
# =========================================================


def resolve_display_profile(
    display_field,
    *,
    mode=None,
    profile=None,
):
    """
    Resolve active DisplayProfile.

    Resolution order
    ----------------

    1. Explicit profile request
    2. Profile matching mode
    3. Sole available profile

    Raises
    ------
    KeyError
        If no suitable profile exists.
    """

    profiles = display_field.profiles

    if not profiles:
        raise KeyError(f"{display_field.field_name}: no display profiles registered")

    # =====================================================
    # Explicit Profile
    # =====================================================

    if profile is not None:
        try:
            return profiles[profile]

        except KeyError as err:
            raise KeyError(f"{display_field.field_name}: profile '{profile}' not found") from err

    # =====================================================
    # Mode-Matched Profile
    # =====================================================

    if mode is not None and mode in profiles:
        return profiles[mode]

    # =====================================================
    # Sole Profile
    # =====================================================

    if len(profiles) == 1:
        return next(
            iter(
                profiles.values(),
            )
        )

    # =====================================================
    # Default Profile
    # =====================================================

    if "default" in profiles:
        return profiles["default"]

    # =====================================================
    # Ambiguous
    # =====================================================

    raise KeyError(
        f"{display_field.field_name}: "
        f"unable to resolve profile "
        f"(mode={mode!r}, profiles={list(profiles)})"
    )
