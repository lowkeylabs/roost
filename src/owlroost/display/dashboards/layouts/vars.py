# src/owlroost/display/dashboards/layouts/vars.py
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
    DashboardRow,
    SummaryPanel,
)
from owlroost.display.specs import (
    DisplayDashboard,
)

# src/owlroost/display/dashboards/layouts/vars.py


def register_display_dashboards(
    reg,
):
    reg.register_dashboard(
        DisplayDashboard(
            name="vars",
            description="Variable inventory dashboard.",
            rows=[
                DashboardRow(
                    [
                        SummaryPanel(
                            title="ROOST Catalog",
                            metric="catalog_size",
                        ),
                        CounterPanel(
                            title="Layer",
                            field_name="layer",
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
                            title="Domain",
                            field_name="semantic_domain",
                        ),
                        CounterPanel(
                            title="Origin",
                            field_name="value_origin",
                        ),
                        CounterPanel(
                            title="Projection",
                            field_name="projection_kind",
                        ),
                    ]
                ),
                DashboardRow(
                    [
                        CounterPanel(
                            title="Analytic",
                            field_name="analytic_kind",
                        ),
                        CounterPanel(
                            title="Level",
                            field_name="materialization_level",
                        ),
                        CounterPanel(
                            title="Type",
                            field_name="node_type",
                        ),
                    ]
                ),
            ],
        )
    )
