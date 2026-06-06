# src/owlroost/display/dashboards/specs.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DashboardRow:
    panels: list


# =====================================================
# Panel Specs
# =====================================================


@dataclass
class SummaryPanel:
    title: str
    metric: str


@dataclass
class CounterPanel:
    title: str
    field_name: str
    sort_by_count: bool = False
    filters: dict[str, object] | None = None


@dataclass
class CrosstabPanel:
    title: str

    row_key: str
    col_key: str

    row_order: list[str] | None = None
    col_order: list[str] | None = None
