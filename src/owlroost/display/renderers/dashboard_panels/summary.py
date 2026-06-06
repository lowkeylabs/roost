# src/owlroost/display/renderers/dashboard_panels/summary.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from rich.align import Align
from rich.text import Text


def render_rich_summary(
    panel,
):
    """
    Render summary panel.
    """

    return Align.center(
        Text(
            str(
                panel.content,
            ),
            justify="center",
        )
    )
