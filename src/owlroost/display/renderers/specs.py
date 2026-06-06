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


# =========================================================
# Dashboard Panel
# =========================================================


# =========================================================
# Dashboard Panel
# =========================================================


@dataclass
class RoostDashboardPanel:
    """
    Renderer-facing dashboard panel.

    A panel owns a single materialized
    content object.

    Currently content may be:

        - text
        - RoostTable

    Future:

        - Crosstab
        - Markdown
        - Chart
        - Tree
        - Text block
    """

    title: str | None = None

    kind: str = "panel"

    content: object | None = None

    width: int | None = None


# =========================================================
# Dashboard Row
# =========================================================


@dataclass
class RoostDashboardRow:
    """
    Horizontal row of dashboard panels.

    Panels are rendered left-to-right.
    """

    panels: list[RoostDashboardPanel]


# =========================================================
# Dashboard
# =========================================================


class RoostDashboard:
    """
    Fully materialized renderer-facing dashboard.

    Dashboards are composed of rows.

    Each row contains one or more panels.

    Example
    -------

    Dashboard

        Row
            Panel
            Panel

        Row
            Panel

        Row
            Panel
            Panel
            Panel
    """

    def __init__(
        self,
        *,
        name: str,
        rows,
        title: str | None = None,
    ):
        self.name = name
        self.title = title or name
        self.rows = rows

    def __repr__(
        self,
    ):
        return f"RoostDashboard(name={self.name!r}, rows={len(self.rows)})"
