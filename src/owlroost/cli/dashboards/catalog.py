# src/owlroost/cli/dashboards/catalog.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
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
    DashboardRow,
    SummaryPanel,
)
from owlroost.display.specs import (
    DisplayDashboard,
)


def register_display_dashboards(
    reg,
):
    reg.register_dashboard(
        DisplayDashboard(
            name="catalog",
            description="Catalog inventory dashboard.",
            rows=[
                DashboardRow(
                    [
                        SummaryPanel(
                            title="ROOST Catalog",
                            metric="catalog_size",
                        ),
                    ]
                ),
                DashboardRow(
                    [
                        CounterPanel(
                            title="Projection Kind",
                            field_name="projection_kind",
                        ),
                        CounterPanel(
                            title="Owner",
                            field_name="owner",
                        ),
                    ]
                ),
                DashboardRow(
                    [
                        CounterPanel(
                            title="Semantic Domain",
                            field_name="semantic_domain",
                        ),
                        CounterPanel(
                            title="Layer",
                            field_name="layer",
                        ),
                        CounterPanel(
                            title="Node Type",
                            field_name="node_type",
                        ),
                    ]
                ),
            ],
        )
    )
