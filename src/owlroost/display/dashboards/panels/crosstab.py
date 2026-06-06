# src/owlroost/display/dashboards/panels/crosstab.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from collections import defaultdict

from owlroost.display.renderers.specs import (
    RoostDashboardPanel,
)


def materialize_crosstab_panel(
    panel_spec,
    *,
    rows,
    registry=None,
    catalog_index=None,
):
    """
    Materialize CrosstabPanel.
    """

    matrix = defaultdict(int)

    for row in rows:
        row_value = row.get(
            panel_spec.row_key,
        )

        col_value = row.get(
            panel_spec.col_key,
        )

        matrix[
            (
                row_value,
                col_value,
            )
        ] += 1

    return RoostDashboardPanel(
        title=panel_spec.title,
        kind="crosstab",
        content={
            "matrix": dict(matrix),
            "row_order": panel_spec.row_order,
            "col_order": panel_spec.col_order,
        },
    )
