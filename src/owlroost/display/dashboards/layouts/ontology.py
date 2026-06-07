# src/owlroost/display/dashboards/layouts/ontology.py
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

from owlroost.display.dashboards.specs import (
    CounterPanel,
    CrosstabPanel,
    DashboardRow,
    SummaryPanel,
)
from owlroost.display.specs import (
    DisplayDashboard,
)

VALUE_ORIGIN_ORDER = [
    "user-specified",
    "owl-computed",
    "roost-computed",
]

OWNER_ORDER = [
    "OWL",
    "ROOST",
]

SEMANTIC_DOMAIN_ORDER = [
    "decision",
    "design",
    "execution",
]

PROJECTION_KIND_ORDER = [
    "canonical",
    "aggregate",
    "composed",
    "synthetic",
    "formatted",
    "alias",
]

LAYER_ORDER = [
    "schema",
    "metrics",
    "display",
]


def register_display_dashboards(
    reg,
):
    reg.register_dashboard(
        DisplayDashboard(
            name="ontology",
            description="Ontology validation dashboard.",
            rows=[
                DashboardRow(
                    [
                        SummaryPanel(
                            title="ROOST Ontology Dashboard",
                            metric="catalog_size",
                        ),
                    ]
                ),
                DashboardRow(
                    [
                        CrosstabPanel(
                            title="Projection Kind × Owner",
                            row_key="projection_kind",
                            col_key="owner",
                            row_order=PROJECTION_KIND_ORDER,
                            col_order=OWNER_ORDER,
                        ),
                        CrosstabPanel(
                            title="Semantic Domain × Owner",
                            row_key="semantic_domain",
                            col_key="owner",
                            row_order=SEMANTIC_DOMAIN_ORDER,
                            col_order=OWNER_ORDER,
                        ),
                    ]
                ),
                DashboardRow(
                    [
                        CrosstabPanel(
                            title="Semantic Domain × Projection Kind",
                            row_key="semantic_domain",
                            col_key="projection_kind",
                            row_order=SEMANTIC_DOMAIN_ORDER,
                            col_order=PROJECTION_KIND_ORDER,
                        ),
                        CrosstabPanel(
                            title="Projection Kind × Value Origin",
                            row_key="projection_kind",
                            col_key="value_origin",
                            row_order=PROJECTION_KIND_ORDER,
                            col_order=VALUE_ORIGIN_ORDER,
                        ),
                    ]
                ),
                DashboardRow(
                    [
                        CrosstabPanel(
                            title="Layer × Owner",
                            row_key="layer",
                            col_key="owner",
                            row_order=LAYER_ORDER,
                            col_order=OWNER_ORDER,
                        ),
                        CounterPanel(
                            title="Lineage Coverage",
                            field_name="derived_from",
                        ),
                        CounterPanel(
                            title="Layer Inventory",
                            field_name="layer",
                        ),
                    ]
                ),
                DashboardRow(
                    [
                        CounterPanel(
                            title="Schema Namespaces",
                            field_name="field_name",
                            sort_by_count=True,
                            filters={
                                "layer": "schema",
                            },
                        ),
                        CounterPanel(
                            title="Metrics Namespaces",
                            field_name="field_name",
                            sort_by_count=True,
                            filters={
                                "layer": "metrics",
                            },
                        ),
                        CounterPanel(
                            title="Display Namespaces",
                            field_name="field_name",
                            sort_by_count=True,
                            filters={
                                "layer": "display",
                            },
                        ),
                    ]
                ),
            ],
        )
    )
