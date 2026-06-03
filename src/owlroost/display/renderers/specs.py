# src/owlroost/display/renderers/specs.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from dataclasses import dataclass

# =========================================================
# Column
# =========================================================


@dataclass
class TableColumn:
    """
    Fully resolved presentation column.

    Notes
    -----
    This object is renderer-facing.

    Materialization is responsible for resolving:

        - labels
        - alignment
        - formatting
        - visibility
        - wrapping metadata
        - explain metadata

    Renderers must not perform:

        - semantic lookups
        - catalog lookups
        - display registry lookups

    All metadata required for rendering and
    explanation should already be attached
    to the column.
    """

    # =====================================================
    # Identity
    # =====================================================

    key: str

    label: str

    # =====================================================
    # Alignment
    # =====================================================

    label_align: str = "left"

    content_align: str = "left"

    # =====================================================
    # Formatting
    # =====================================================

    wrap: bool = False

    fmt: str | None = None

    # =====================================================
    # Layout
    # =====================================================

    width: int | None = None

    # =====================================================
    # Explain Metadata
    #
    # Attached during materialization so
    # explain systems do not need access
    # to registries or catalogs.
    # =====================================================

    field_name: str | None = None

    display_field: object | None = None

    catalog_spec: object | None = None


# =========================================================
# Table
# =========================================================


class RoostTable:
    """
    Fully materialized renderer-facing table.

    This object intentionally contains:
    - no schema logic
    - no aggregation logic
    - no dataset logic

    It is the stable contract between:
    - materializers
    - pivot transforms
    - renderers
    """

    def __init__(
        self,
        columns,
        rows,
        row_meta=None,
    ):
        self.columns = columns
        self.rows = rows
        self.row_meta = row_meta or []

    # =====================================================
    # Diagnostics
    # =====================================================

    @property
    def column_labels(self):
        return [c.label for c in self.columns]

    @property
    def column_keys(self):
        return [c.key for c in self.columns]

    # =====================================================
    # Representation
    # =====================================================

    def __repr__(self):
        return f"RoostTable(columns={len(self.columns)}, rows={len(self.rows)})"


# =========================================================
# Backward Compatibility Alias
# =========================================================

# Temporary compatibility during migration.
Table = RoostTable
