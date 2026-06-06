# src/owlroost/display/dashboards/panels/counter.py

from __future__ import annotations

from collections import Counter

from owlroost.display.dashboards.specs import (
    CounterPanel,
)
from owlroost.display.renderers.specs import (
    RoostTable,
    TableColumn,
)

PANEL_SPEC = CounterPanel


def materialize(
    panel_spec,
    *,
    rows,
    registry=None,
    catalog_index=None,
):
    """
    Materialize CounterPanel.

    Returns
    -------
    RoostTable
    """

    counts = Counter()

    filters = panel_spec.filters or {}

    for row in rows:
        if any(row.get(key) != value for key, value in filters.items()):
            continue

        value = row.get(
            panel_spec.field_name,
        )

        # =============================================
        # Missing
        # =============================================

        if value is None:
            counts["<none>"] += 1

        # =============================================
        # Collections
        # =============================================

        elif isinstance(
            value,
            (list, tuple, set),
        ):
            if not value:
                counts["<empty>"] += 1

            else:
                for item in value:
                    counts[item] += 1

        # =============================================
        # Scalars
        # =============================================

        else:
            counts[value] += 1

    items = list(
        counts.items(),
    )

    if panel_spec.sort_by_count:
        items.sort(
            key=lambda x: x[1],
            reverse=True,
        )

    else:
        items.sort(
            key=lambda x: str(
                x[0],
            ),
        )

    return RoostTable(
        columns=[
            TableColumn(
                key="value",
                label="Value",
            ),
            TableColumn(
                key="count",
                label="Count",
                content_align="right",
            ),
        ],
        rows=[[value, count] for value, count in items],
    )
