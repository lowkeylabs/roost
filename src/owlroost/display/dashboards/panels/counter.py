# src/owlroost/display/dashboards/panels/counter.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from collections import Counter

from owlroost.display.renderers.specs import (
    RoostDashboardPanel,
)


def materialize_counter_panel(
    panel_spec,
    *,
    rows,
    registry=None,
    catalog_index=None,
):
    """
    Materialize CounterPanel.

    Notes
    -----
    Supports both:

        scalar fields
            owner
            layer
            projection_kind

    and

        collection fields
            derived_from

    Collection values contribute one count
    per element.
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
        # Collection Values
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
        # Scalar Values
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

    return RoostDashboardPanel(
        title=panel_spec.title,
        kind="counter",
        content=items,
    )
