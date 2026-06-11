# src/owlroost/display/dashboards/panels/counter.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from collections import Counter

from owlroost.catalog.ontology import (
    get_ontology_dimension,
)
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

    # =====================================================
    # Ontology Ordering
    # =====================================================

    dimension = get_ontology_dimension(
        panel_spec.field_name,
    )

    if dimension is not None:
        # =============================================
        # Ensure all ontology values appear
        # =============================================

        for value in dimension.values:
            counts.setdefault(
                value,
                0,
            )

        # =============================================
        # Hide synthetic QA values when empty
        # =============================================

        if (
            counts.get(
                "<none>",
                0,
            )
            == 0
        ):
            counts.pop(
                "<none>",
                None,
            )

        if (
            counts.get(
                "<empty>",
                0,
            )
            == 0
        ):
            counts.pop(
                "<empty>",
                None,
            )

        items = list(
            counts.items(),
        )

        # =============================================
        # Ontology-defined ordering
        # =============================================

        ordered_values = list(
            dimension.values,
        )

        if "<none>" in counts:
            ordered_values.append(
                "<none>",
            )

        if "<empty>" in counts:
            ordered_values.append(
                "<empty>",
            )

        order = {
            value: index
            for index, value in enumerate(
                ordered_values,
            )
        }

        items.sort(
            key=lambda x: (
                order.get(
                    x[0],
                    9999,
                ),
                str(
                    x[0],
                ),
            )
        )

    # =====================================================
    # Count Ordering
    # =====================================================

    elif panel_spec.sort_by_count:
        items.sort(
            key=lambda x: x[1],
            reverse=True,
        )

    # =====================================================
    # Alphabetical Ordering
    # =====================================================

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
