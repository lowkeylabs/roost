# src/owlroost/display/table.py

from __future__ import annotations

from dataclasses import dataclass

# =========================================================
# Column
# =========================================================


@dataclass
class TableColumn:
    """
    Fully resolved presentation column.

    This object is renderer-facing.

    Materialization is responsible for resolving:
    - labels
    - alignment
    - formatting
    - visibility

    Renderers should not perform semantic lookups.
    """

    key: str

    label: str

    label_align: str = "left"
    content_align: str = "left"

    fmt: str | None = None


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
    ):
        self.columns = columns

        self.rows = rows

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
        return "RoostTable(" f"columns={len(self.columns)}, " f"rows={len(self.rows)}" ")"


# =========================================================
# Backward Compatibility Alias
# =========================================================

# Temporary compatibility during migration.
Table = RoostTable
