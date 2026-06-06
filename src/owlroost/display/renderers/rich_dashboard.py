# src/owlroost/display/renderers/rich_dashboard.py

"""
Dashboard renderer.

Notes
-----
Temporary renderer used during dashboard
subsystem migration.

Architectural Invariant
-----------------------

Renderers consume renderer-facing
RoostDashboard objects.

Renderers do not access:

    - schema registry
    - metrics registry
    - display registry

All dashboard semantics should already
be materialized.
"""

from __future__ import annotations

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel

from owlroost.display.renderers.dashboard_panels.render import (
    render_rich_panel,
)


def render_rich_dashboard(
    dashboard,
):
    """
    Render dashboard.

    Current implementation is intentionally
    simple and exists primarily to validate
    dashboard discovery, registration,
    materialization, and rendering
    pipelines.
    """

    console = Console()

    title = getattr(
        dashboard,
        "title",
        dashboard.name,
    )

    console.rule(title)

    for row in dashboard.rows:
        renderables = []

        for panel in row.panels:
            renderables.append(
                Panel(
                    render_rich_panel(
                        panel,
                    ),
                    title=panel.title,
                    expand=True,
                    # width=40,
                )
            )

        console.print(
            Columns(
                renderables,
                expand=True,
                equal=True,
            )
        )

        console.print()

    return ""
