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

Renderers consume RoostDashboard objects.

Architectural Invariant
-----------------------

Materializers do not render.

Materializers do not import Rich.

Materializers resolve dashboard layout
definitions into renderer-neutral objects.
"""

from __future__ import annotations

from owlroost.display.dashboards.panels import (
    materialize_counter_panel,
    materialize_crosstab_panel,
    materialize_summary_panel,
)
from owlroost.display.dashboards.specs import (
    CounterPanel,
    CrosstabPanel,
    SummaryPanel,
)
from owlroost.display.renderers.specs import (
    RoostDashboard,
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
        panels = []

        for panel_spec in row_spec.panels:
            # =============================================
            # Summary Panel
            # =============================================

            if isinstance(
                panel_spec,
                SummaryPanel,
            ):
                panel = materialize_summary_panel(
                    panel_spec,
                    rows=rows,
                    registry=registry,
                    catalog_index=catalog_index,
                )

            # =============================================
            # Counter Panel
            # =============================================

            elif isinstance(
                panel_spec,
                CounterPanel,
            ):
                panel = materialize_counter_panel(
                    panel_spec,
                    rows=rows,
                    registry=registry,
                    catalog_index=catalog_index,
                )

            # =============================================
            # Crosstab Panel
            # =============================================

            elif isinstance(
                panel_spec,
                CrosstabPanel,
            ):
                panel = materialize_crosstab_panel(
                    panel_spec,
                    rows=rows,
                    registry=registry,
                    catalog_index=catalog_index,
                )

            # =============================================
            # Unknown Panel
            # =============================================

            else:
                raise TypeError(f"Unsupported dashboard panel: {type(panel_spec).__name__}")

            panels.append(
                panel,
            )

        dashboard_rows.append(
            RoostDashboardRow(
                panels=panels,
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
