# src/owlroost/display/renderers/specs.py

"""
Renderer-facing display specifications.

Notes
-----
Defines renderer-neutral presentation
objects produced by materializers and
consumed by renderers.

Architectural Invariant
-----------------------

Renderers consume only renderer-facing
objects.

Renderers must not perform:

    - schema lookups
    - catalog lookups
    - display registry lookups

All presentation metadata should already
be resolved during materialization.
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
    Materialization is responsible for
    resolving:

        - labels
        - alignment
        - formatting
        - visibility
        - wrapping metadata
        - explain metadata

    Renderers should not consult
    registries or ontologies.
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
        - transforms
        - renderers

    Notes
    -----
    Summary panels, counters, crosstabs,
    compare tables, pivots, and ordinary
    tables should all ultimately become
    RoostTable instances.
    """

    def __init__(
        self,
        columns,
        rows,
        row_meta=None,
        *,
        show_header=True,
        title=None,
    ):
        self.columns = columns
        self.rows = rows

        self.row_meta = row_meta or []

        self.show_header = show_header

        self.title = title

    # =====================================================
    # Diagnostics
    # =====================================================

    @property
    def column_labels(
        self,
    ):
        return [c.label for c in self.columns]

    @property
    def column_keys(
        self,
    ):
        return [c.key for c in self.columns]

    # =====================================================
    # Representation
    # =====================================================

    def __repr__(
        self,
    ):
        return f"RoostTable(columns={len(self.columns)}, rows={len(self.rows)})"


# =========================================================
# Backward Compatibility Alias
# =========================================================

Table = RoostTable


# =========================================================
# Dashboard Panel
# =========================================================


@dataclass
class RoostDashboardPanel:
    """
    Renderer-facing dashboard panel.

    Panels own a single materialized
    presentation object.

    Currently expected content:

        - RoostTable

    Future possibilities:

        - RoostChart
        - RoostTree
        - RoostMarkdown

    Dashboard layout owns panel placement.

    Content owns presentation semantics.
    """

    title: str | None = None

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
    Fully materialized renderer-facing
    dashboard.

    Dashboards are composed of rows.

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
