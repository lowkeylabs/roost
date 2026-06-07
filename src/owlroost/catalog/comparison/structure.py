# src/owlroost/catalog/comparison/structure.py
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

from copy import deepcopy
from pathlib import Path

# =========================================================
# Constants
# =========================================================

STRUCTURAL_COMPARE_EXCLUDES = {
    "description",
    "promotion",
}

# =========================================================
# Helpers
# =========================================================


def format_nested_list(
    value,
    indent=0,
):
    """
    Recursively format nested lists
    with line breaks.
    """

    # =====================================================
    # Non-list
    # =====================================================

    if not isinstance(value, list):
        if isinstance(value, float):
            return f"{value:g}"

        return str(value)

    # =====================================================
    # Flat list
    # =====================================================

    if not any(isinstance(x, list) for x in value):
        inner = ", ".join(format_nested_list(x) for x in value)

        return f"[{inner}]"

    # =====================================================
    # Nested list
    # =====================================================

    lines = []

    for item in value:
        lines.append(
            format_nested_list(
                item,
                indent + 2,
            )
        )

    return "\n".join(lines)


def format_compare_value(
    value,
):
    """
    Format arbitrary TOML value for comparison display.
    """

    if value is None:
        return ""

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, float):
        return f"{value:g}"

    # -----------------------------------------------------
    # Path-like strings
    # -----------------------------------------------------

    if isinstance(value, str):
        # ---------------------------------------------
        # Show only basename for TOML files
        # ---------------------------------------------

        if value.endswith(".toml"):
            return str(Path(value).name)

        return value

    if isinstance(value, list):
        return format_nested_list(
            value,
        )

    return str(value)


def flatten_structure(
    obj,
    prefix="",
    out=None,
    seen_sections=None,
):
    """
    Flatten nested TOML dict structure while preserving
    TOML ordering.

    Produces entries:

        ("section", "basic_info")
        ("field", "basic_info.status")

    Sections emitted only once.
    """

    if out is None:
        out = []

    if seen_sections is None:
        seen_sections = set()

    if not isinstance(obj, dict):
        return out

    for key, value in obj.items():
        full = key if not prefix else f"{prefix}.{key}"

        if isinstance(value, dict):
            if full not in seen_sections:
                out.append(
                    (
                        "section",
                        full,
                    )
                )

                seen_sections.add(full)

            flatten_structure(
                value,
                prefix=full,
                out=out,
                seen_sections=seen_sections,
            )

        else:
            out.append(
                (
                    "field",
                    full,
                )
            )

    return out


def resolve_path(
    obj,
    path,
):
    """
    Resolve dotted path from nested dict.

    Returns None if missing.
    """

    current = obj

    for part in path.split("."):
        if not isinstance(
            current,
            dict,
        ):
            return None

        if part not in current:
            return None

        current = current[part]

    return current


def values_differ(
    values,
):
    """
    Return True if values differ across rows.
    """

    normalized = [deepcopy(v) for v in values]

    first = normalized[0]

    for value in normalized[1:]:
        if value != first:
            return True

    return False


# =========================================================
# Compare Matrix
# =========================================================


def build_compare_entries(
    rows,
    diff_only=False,
):
    """
    Build ordered comparison entry structure.

    Preserves TOML hierarchy and ordering.
    """

    if not rows:
        return []

    ordered_entries = []

    seen_entries = set()

    for row in rows:
        inputs = row.get(
            "_inputs",
            {},
        )

        entries = flatten_structure(
            inputs,
        )

        for entry in entries:
            if entry in seen_entries:
                continue

            ordered_entries.append(
                entry,
            )

            seen_entries.add(
                entry,
            )

    materialized = []

    emitted_sections = set()

    for kind, value in ordered_entries:
        if kind == "section":
            continue

        if kind != "field":
            continue

        parts = value.split(".")

        if value in STRUCTURAL_COMPARE_EXCLUDES:
            continue

        if any(part in STRUCTURAL_COMPARE_EXCLUDES for part in parts):
            continue

        if "." in value:
            section_name, field_name = value.rsplit(
                ".",
                1,
            )

        else:
            section_name = "_root"
            field_name = value

        vals = []

        for row in rows:
            vals.append(
                resolve_path(
                    row.get(
                        "_inputs",
                        {},
                    ),
                    value,
                )
            )

        if diff_only and not values_differ(vals):
            continue

        if section_name != "_root" and section_name not in emitted_sections:
            emitted_sections.add(
                section_name,
            )

            materialized.append(
                {
                    "kind": "section",
                    "label": section_name,
                }
            )

        materialized.append(
            {
                "kind": "field",
                "path": value,
                "section": section_name,
                "field_name": field_name,
                "values": vals,
            }
        )

    return materialized


# =========================================================
# Equivalence
# =========================================================


def rows_are_equivalent(
    row_a,
    row_b,
):
    """
    Return True if two rows are structurally equivalent.

    Uses exactly the same semantics as diff_only.
    """

    entries = build_compare_entries(
        [
            row_a,
            row_b,
        ],
        diff_only=True,
    )

    return len(entries) == 0
