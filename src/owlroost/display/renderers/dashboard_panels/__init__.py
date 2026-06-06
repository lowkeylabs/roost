# src/owlroost/display/renderers/dashboard_panels/__init__.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from .counter import render_rich_counter
from .crosstab import render_rich_crosstab
from .summary import render_rich_summary

__all__ = [
    "render_rich_summary",
    "render_rich_counter",
    "render_rich_crosstab",
]
