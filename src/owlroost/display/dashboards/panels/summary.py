# src/owlroost/display/dashboards/panels/summary.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.display.renderers.specs import (
    RoostDashboardPanel,
)


def materialize_summary_panel(
    panel_spec,
    *,
    rows,
    registry=None,
    catalog_index=None,
):
    """
    Materialize SummaryPanel.
    """

    if panel_spec.metric == "catalog_size":
        value = f"Catalog size: {len(rows)}"

    else:
        value = None

    return RoostDashboardPanel(
        title=panel_spec.title,
        kind="summary",
        content=value,
    )
