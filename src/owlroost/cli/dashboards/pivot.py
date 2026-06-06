# src/owlroost/cli/dashboards/pivot.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.display.dashboards.specs import (
    CrosstabPanel,
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
            name="pivot",
            description="Ontology pivot dashboard.",
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
                        CrosstabPanel(
                            title="Projection Kind × Owner",
                            row_key="projection_kind",
                            col_key="owner",
                        ),
                        CrosstabPanel(
                            title="Semantic Domain × Owner",
                            row_key="semantic_domain",
                            col_key="owner",
                        ),
                    ]
                ),
                DashboardRow(
                    [
                        CrosstabPanel(
                            title="Layer × Owner",
                            row_key="layer",
                            col_key="owner",
                        ),
                        CrosstabPanel(
                            title="Node Type × Projection",
                            row_key="node_type",
                            col_key="projection_kind",
                        ),
                    ]
                ),
            ],
        )
    )
