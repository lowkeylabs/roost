# src/owlroost/display/operations/resolution.py
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

# =========================================================
# Path Extraction
# =========================================================


def extract_path(
    data,
    path,
):
    """
    Extract dotted path from nested dictionaries.
    """

    if data is None:
        return None

    if path == "_path":
        return str(data["_path"])

    cur = data

    for p in path.split("."):
        if not isinstance(cur, dict):
            return None

        cur = cur.get(p)

        if cur is None:
            return None

    return cur


# =========================================================
# Semantic Field Resolution
# =========================================================


def resolve_field_value(
    row,
    field_name,
    display_field=None,
):
    """
    Resolve semantic field value from row.

    Resolution order:
        1. display_fn
        2. explicit display path
        3. _metrics
        4. _meta
        5. _inputs
        6. top-level row
    """

    # =====================================================
    # Display-derived value
    # =====================================================

    if display_field is not None and display_field.display_fn:
        return display_field.display_fn(row)

    # =====================================================
    # Explicit display path
    # =====================================================

    if display_field is not None and display_field.path is not None:
        value = extract_path(
            row,
            display_field.path,
        )

        if value is not None:
            return value

    # =====================================================
    # Metrics
    # =====================================================

    metrics = row.get("_metrics", {})

    if field_name in metrics:
        return metrics[field_name]

    # =====================================================
    # Meta
    # =====================================================

    meta = row.get("_meta", {})

    if field_name in meta:
        return meta[field_name]

    # =====================================================
    # Inputs
    # =====================================================

    value = extract_path(
        row.get("_inputs", {}),
        field_name,
    )

    if value is not None:
        return value

    # =====================================================
    # Top-level row
    # =====================================================

    return row.get(field_name)


# =========================================================
# Row Value Resolution
# =========================================================


def resolve_row_value(
    row,
    key,
):
    """
    Resolve value from operational row.

    Search order:
        _meta
        _metrics
        top-level row
        _inputs
    """

    # =====================================================
    # Synthetic aliases
    # =====================================================

    if key == "id":
        return row.get(
            "_row_id",
        )

    # =====================================================
    # _meta
    # =====================================================

    meta = row.get(
        "_meta",
        {},
    )

    if key in meta:
        return meta[key]

    # =====================================================
    # _metrics
    # =====================================================

    metrics = row.get(
        "_metrics",
        {},
    )

    if key in metrics:
        return metrics[key]

    # =====================================================
    # Top-level row
    # =====================================================

    if key in row:
        return row[key]

    # =====================================================
    # _inputs dotted-path lookup
    # =====================================================

    current = row.get(
        "_inputs",
        {},
    )

    for part in key.split("."):
        if not isinstance(
            current,
            dict,
        ):
            return None

        if part not in current:
            return None

        current = current[part]

    return current
