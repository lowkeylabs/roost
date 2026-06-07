# src/owlroost/display/renderers/rich_dashboard.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Dashboard renderer.

Notes
-----
Render renderer-facing dashboards.

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

from owlroost.display.renderers.rich_table import (
    build_rich_table,
)


def render_rich_dashboard(
    dashboard,
):
    """
    Render dashboard.
    """

    console = Console()

    title = getattr(
        dashboard,
        "title",
        dashboard.name,
    )

    console.rule(
        title,
    )

    for row in dashboard.rows:
        renderables = []

        for panel in row.panels:
            renderables.append(
                Panel(
                    build_rich_table(
                        panel.content,
                    ),
                    title=panel.title,
                    expand=True,
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
