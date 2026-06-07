# src/owlroost/display/explain/facets/display.py
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

FACET_NAME = "display"


def render(
    *,
    display_field,
    catalog_row,
    row_values,
) -> str:
    """
    Display facet.

    Notes
    -----
    Intended primarily as a developer aid.

    Answers:

        - Where is this display field defined?
        - If auto-created, where should a
          definition be added?
        - What display profiles exist?
    """

    if display_field is None:
        return "DisplayField: AUTO-CREATED\nSuggested File: display/fields/"

    lines = []

    # =====================================================
    # Definition Location
    # =====================================================

    defined_in = getattr(
        display_field,
        "defined_in",
        None,
    )

    field_name = getattr(
        display_field,
        "field_name",
        "",
    )

    if defined_in:
        lines.append(f"Defined In: {defined_in}")

    else:
        lines.append("Defined In: AUTO-CREATED")

        namespace = field_name.split(".")[0] if field_name else "custom"

        lines.append(f"Suggested File: display/fields/{namespace}.py")

    # =====================================================
    # Profiles
    # =====================================================

    profiles = getattr(
        display_field,
        "profiles",
        {},
    )

    if profiles:
        lines.append("")

        for name, profile in sorted(
            profiles.items(),
        ):
            attrs = []

            if profile.label:
                attrs.append(f"label={profile.label}")

            if profile.width is not None:
                attrs.append(f"width={profile.width}")

            if profile.fmt:
                attrs.append(f"fmt={profile.fmt}")

            if profile.content_align and profile.content_align != "left":
                attrs.append(f"align={profile.content_align}")

            if profile.wrap:
                attrs.append(f"wrap={profile.wrap}")

            if profile.visible is not True:
                attrs.append(f"visible={profile.visible}")

            if attrs:
                lines.append(f"{name}(" + ", ".join(attrs) + ")")

            else:
                lines.append(f"{name}()")

    return "\n".join(
        lines,
    )
