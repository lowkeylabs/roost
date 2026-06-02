# src/owlroost/cli/dashboards/catalog.py

"""
Catalog dashboard.

Notes
-----
Default landing page for:

    roost vars

Summarizes catalog contents using
Rich panels.

This module intentionally operates
directly on catalog rows and does not
use:

    - DisplayView
    - DisplayField
    - RoostTable
    - materialize_view()
"""

from __future__ import annotations

from collections import Counter, defaultdict

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# =========================================================
# Helpers
# =========================================================

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


def _build_counter_panel(
    title,
    counter,
    *,
    sort_by_count=False,
):
    """
    Render a Counter as a Rich panel.
    """

    table = Table(
        show_header=False,
        box=None,
        pad_edge=False,
    )

    table.add_column(
        justify="left",
    )

    table.add_column(
        justify="right",
    )

    if sort_by_count:
        items = sorted(
            counter.items(),
            key=lambda x: (
                -x[1],
                x[0],
            ),
        )

    else:
        items = sorted(
            counter.items(),
        )

    for key, count in items:
        table.add_row(
            str(key),
            f"{count:,}",
        )

    return Panel(
        table,
        title=title,
    )


def build_namespace_counts(
    rows,
):
    """
    Count top-level field namespaces.
    """

    counts = Counter()

    for row in rows:
        field_name = row.get(
            "field_name",
            "",
        )

        if not field_name:
            continue

        namespace = field_name.split(
            ".",
            1,
        )[0]

        counts[namespace] += 1

    return counts


# =========================================================
# Crosstab Helpers
# =========================================================


def _build_crosstab_panel(
    rows,
    *,
    row_key,
    col_key,
    title,
    row_order=None,
    col_order=None,
):
    """
    Build a simple count crosstab.
    """

    counts = defaultdict(int)

    row_values = set()

    col_values = set()

    # =====================================================
    # Collect values
    # =====================================================

    for row in rows:
        r = row.get(
            row_key,
            "unknown",
        )

        c = row.get(
            col_key,
            "unknown",
        )

        row_values.add(
            r,
        )

        col_values.add(
            c,
        )

        counts[(r, c)] += 1

    # =====================================================
    # Apply ordering
    # =====================================================

    if row_order:
        ordered = [value for value in row_order if value in row_values]

        ordered.extend(sorted(row_values - set(row_order)))

        row_values = ordered

    else:
        row_values = sorted(
            row_values,
        )

    if col_order:
        ordered = [value for value in col_order if value in col_values]

        ordered.extend(sorted(col_values - set(col_order)))

        col_values = ordered

    else:
        col_values = sorted(
            col_values,
        )

    # =====================================================
    # Render table
    # =====================================================

    table = Table(
        box=None,
        pad_edge=False,
    )

    table.add_column(
        row_key,
        justify="left",
    )

    for value in col_values:
        table.add_column(
            str(value),
            justify="right",
        )

    for r in row_values:
        row_data = [
            str(r),
        ]

        for c in col_values:
            row_data.append(
                str(
                    counts.get(
                        (r, c),
                        0,
                    )
                )
            )

        table.add_row(
            *row_data,
        )

    return Panel(
        table,
        title=title,
    )


# =========================================================
# Dashboard
# =========================================================


def render_catalog_dashboard(
    rows,
):
    """
    Render catalog summary dashboard.
    """

    console = Console()

    # =====================================================
    # Counters
    # =====================================================

    projection_counts = Counter(
        row.get(
            "projection_kind",
            "unknown",
        )
        for row in rows
    )

    owner_counts = Counter(
        row.get(
            "owner",
            "unknown",
        )
        for row in rows
    )

    domain_counts = Counter(
        row.get(
            "semantic_domain",
            "unknown",
        )
        for row in rows
    )

    layer_counts = Counter(
        row.get(
            "layer",
            "unknown",
        )
        for row in rows
    )

    node_type_counts = Counter(
        row.get(
            "node_type",
            "unknown",
        )
        for row in rows
    )

    # =====================================================
    # Header
    # =====================================================

    total_variables = len(
        rows,
    )

    console.print()

    console.print(
        Panel(
            f"[bold]{total_variables:,}[/bold] catalog variables",
            title="ROOST Catalog",
        )
    )

    console.print()

    # =====================================================
    # Top Row
    # =====================================================

    console.print(
        Columns(
            [
                _build_counter_panel(
                    "Projection Kind",
                    projection_counts,
                ),
                _build_counter_panel(
                    "Owner",
                    owner_counts,
                ),
            ]
        )
    )

    # =====================================================
    # Bottom Row
    # =====================================================

    console.print(
        Columns(
            [
                _build_counter_panel(
                    "Semantic Domain",
                    domain_counts,
                ),
                _build_counter_panel(
                    "Layer",
                    layer_counts,
                ),
                _build_counter_panel(
                    "Node Type",
                    node_type_counts,
                ),
            ]
        )
    )

    console.print()


# =========================================================
# Pivot Dashboard
# =========================================================


def render_catalog_pivot_dashboard(
    rows,
):
    """
    Render ontology-oriented dashboard.
    """

    console = Console()

    total_variables = len(
        rows,
    )

    console.print()

    console.print(
        Panel(
            f"[bold]{total_variables:,}[/bold] catalog variables",
            title="ROOST Catalog",
        )
    )

    console.print()

    console.print(
        Columns(
            [
                _build_crosstab_panel(
                    rows,
                    row_key="projection_kind",
                    col_key="owner",
                    title="Projection Kind × Owner",
                ),
                _build_crosstab_panel(
                    rows,
                    row_key="semantic_domain",
                    col_key="owner",
                    title="Semantic Domain × Owner",
                ),
            ]
        )
    )

    console.print()

    console.print(
        Columns(
            [
                _build_crosstab_panel(
                    rows,
                    row_key="layer",
                    col_key="owner",
                    title="Layer × Owner",
                ),
                _build_crosstab_panel(
                    rows,
                    row_key="node_type",
                    col_key="projection_kind",
                    title="Node Type × Projection",
                ),
            ]
        )
    )

    console.print()


# =========================================================
# Ontology Dashboard
# =========================================================


def render_catalog_ontology_dashboard(
    rows,
):
    """
    Render ontology validation dashboard.

    Focuses on validating relationships
    between ontology dimensions.
    """

    console = Console()

    total_variables = len(
        rows,
    )

    # =====================================================
    # Lineage Coverage
    # =====================================================

    lineage_present = sum(
        1
        for row in rows
        if row.get(
            "derived_from",
        )
    )

    lineage_missing = total_variables - lineage_present

    lineage_panel = _build_counter_panel(
        "Lineage Coverage",
        Counter(
            {
                "present": lineage_present,
                "missing": lineage_missing,
            }
        ),
    )

    # =====================================================
    # Layer Inventory
    # =====================================================

    layer_panel = _build_counter_panel(
        "Layer Inventory",
        Counter(
            row.get(
                "layer",
                "unknown",
            )
            for row in rows
        ),
    )

    # =====================================================
    # Namespace Inventories
    # =====================================================

    schema_namespace_panel = _build_counter_panel(
        "Schema Namespaces",
        build_namespace_counts(
            [row for row in rows if row.get("layer") == "schema"],
        ),
        sort_by_count=True,
    )

    metrics_namespace_panel = _build_counter_panel(
        "Metrics Namespaces",
        build_namespace_counts(
            [row for row in rows if row.get("layer") == "metrics"],
        ),
        sort_by_count=True,
    )

    display_namespace_panel = _build_counter_panel(
        "Display Namespaces",
        build_namespace_counts(
            [row for row in rows if row.get("layer") == "display"],
        ),
        sort_by_count=True,
    )

    # =====================================================
    # Header
    # =====================================================

    console.print()

    console.print(
        Panel(
            f"[bold]{total_variables:,}[/bold] catalog variables",
            title="ROOST Ontology Dashboard",
        )
    )

    console.print()

    # =====================================================
    # Row 1
    # =====================================================

    console.print(
        Columns(
            [
                _build_crosstab_panel(
                    rows,
                    row_key="projection_kind",
                    col_key="owner",
                    row_order=PROJECTION_KIND_ORDER,
                    col_order=OWNER_ORDER,
                    title="Projection Kind × Owner",
                ),
                _build_crosstab_panel(
                    rows,
                    row_key="semantic_domain",
                    col_key="owner",
                    row_order=SEMANTIC_DOMAIN_ORDER,
                    col_order=OWNER_ORDER,
                    title="Semantic Domain × Owner",
                ),
            ]
        )
    )

    console.print()

    # =====================================================
    # Row 2
    # =====================================================

    console.print(
        Columns(
            [
                _build_crosstab_panel(
                    rows,
                    row_key="semantic_domain",
                    col_key="projection_kind",
                    row_order=SEMANTIC_DOMAIN_ORDER,
                    col_order=PROJECTION_KIND_ORDER,
                    title="Semantic Domain × Projection Kind",
                ),
                _build_crosstab_panel(
                    rows,
                    row_key="projection_kind",
                    col_key="value_origin",
                    row_order=PROJECTION_KIND_ORDER,
                    col_order=VALUE_ORIGIN_ORDER,
                    title="Projection Kind × Value Origin",
                ),
            ]
        )
    )

    console.print()

    # =====================================================
    # Row 3
    # =====================================================

    console.print(
        Columns(
            [
                _build_crosstab_panel(
                    rows,
                    row_key="layer",
                    col_key="owner",
                    row_order=LAYER_ORDER,
                    col_order=OWNER_ORDER,
                    title="Layer × Owner",
                ),
                lineage_panel,
                layer_panel,
            ]
        )
    )

    console.print()

    # =====================================================
    # Row 4
    # =====================================================

    console.print(
        Columns(
            [
                schema_namespace_panel,
                metrics_namespace_panel,
                display_namespace_panel,
            ]
        )
    )

    console.print()
