# src/owlroost/display/renderers/dashboard_panels/render.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.display.renderers.dashboard_panels import (
    render_rich_counter,
    render_rich_crosstab,
    render_rich_summary,
)


def render_rich_panel(
    panel,
):
    """
    Dispatch dashboard panel rendering.
    """

    if panel.kind == "summary":
        return render_rich_summary(
            panel,
        )

    if panel.kind == "counter":
        return render_rich_counter(
            panel,
        )

    if panel.kind == "crosstab":
        return render_rich_crosstab(
            panel,
        )

    return repr(
        panel.content,
    )
