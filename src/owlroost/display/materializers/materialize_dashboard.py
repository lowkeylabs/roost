# src/owlroost/display/materializers/materialize_dashboard.py

"""
Dashboard materialization.

Notes
-----
Transforms declarative DisplayDashboard
definitions into renderer-facing dashboard
objects.

Architecture
------------
DisplayDashboard
    -> DashboardRow
        -> Panel Spec

becomes

RoostDashboard
    -> RoostDashboardRow
        -> RoostDashboardPanel

Panel-specific computation is delegated
to dashboard panel plugins discovered
from:

    display.dashboards.panels

Architectural Invariant
-----------------------

Materializers do not render.

Materializers do not import Rich.

Materializers resolve dashboard layout
definitions into renderer-neutral objects.
"""

from __future__ import annotations

from owlroost.display.dashboards.panels import get_panel_materializer
from owlroost.display.renderers.specs import (
    RoostDashboard,
    RoostDashboardPanel,
    RoostDashboardRow,
)

# =========================================================
# Dashboard Materialization
# =========================================================


def materialize_dashboard(
    dashboard,
    *,
    rows,
    registry=None,
    catalog_index=None,
):
    """
    Materialize dashboard.

    Parameters
    ----------
    dashboard
        DisplayDashboard definition.

    rows
        Catalog rows.

    registry
        DisplayRegistry.

    Returns
    -------
    RoostDashboard
    """

    dashboard_rows = []

    for row_spec in dashboard.rows:
        materialized_panels = []

        for panel_spec in row_spec.panels:
            panel_type = type(
                panel_spec,
            )

            materializer = get_panel_materializer(
                type(panel_spec),
            )

            if materializer is None:
                raise TypeError(f"No dashboard materializer registered for {panel_type.__name__}")

            content = materializer(
                panel_spec,
                rows=rows,
                registry=registry,
                catalog_index=catalog_index,
            )

            materialized_panels.append(
                RoostDashboardPanel(
                    title=panel_spec.title,
                    content=content,
                )
            )

        dashboard_rows.append(
            RoostDashboardRow(
                panels=materialized_panels,
            )
        )

    return RoostDashboard(
        name=dashboard.name,
        title=getattr(
            dashboard,
            "title",
            dashboard.name,
        ),
        rows=dashboard_rows,
    )
