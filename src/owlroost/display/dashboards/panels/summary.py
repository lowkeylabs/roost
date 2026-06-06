# src/owlroost/display/dashboards/panels/summary.py

from __future__ import annotations

from owlroost.display.dashboards.specs import (
    SummaryPanel,
)
from owlroost.display.renderers.specs import (
    RoostTable,
    TableColumn,
)

PANEL_SPEC = SummaryPanel


def materialize(
    panel_spec,
    *,
    rows,
    registry=None,
    catalog_index=None,
):
    """
    Materialize SummaryPanel.

    Returns
    -------
    RoostTable
    """

    if panel_spec.metric == "catalog_size":
        value = len(
            rows,
        )

    else:
        value = None

    return RoostTable(
        columns=[
            TableColumn(
                key="value",
                label="Value",
                content_align="right",
            ),
        ],
        rows=[
            [value],
        ],
    )
