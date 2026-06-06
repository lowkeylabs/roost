# src/owlroost/cli/cmd_vars.py

"""
TODO: Document module.

Notes
-----
Display canonical catalog semantics.

Architecture
------------
Schema Registry
    -> Metrics Registry
    -> Display Registry
    -> Catalog Rows
    -> Materialized View
    -> RoostTable
    -> Renderer
"""

from __future__ import annotations

import click

from owlroost.catalog.loaders import load_catalog_rows
from owlroost.cli.dashboards.catalog import (
    render_catalog_dashboard,
    render_catalog_ontology_dashboard,
    render_catalog_pivot_dashboard,
)
from owlroost.cli.utils import render_table, resolve_renderer, select_rows_by_id, split_catalog_args
from owlroost.display.bootstrap import build_display_registry
from owlroost.display.explain import parse_explain_request
from owlroost.display.materializers.materialize import materialize_view
from owlroost.display.operations.filtering import apply_filters
from owlroost.display.operations.help import render_field_help
from owlroost.display.operations.row_ops import apply_top, attach_row_ids
from owlroost.display.operations.sorting import apply_canonical_sort, apply_sort
from owlroost.display.operations.table_ops import inject_id_column
from owlroost.metrics.bootstrap import build_metrics_registry
from owlroost.schema.bootstrap import build_schema_registry

# =========================================================
# Defaults
# =========================================================

DEFAULT_LEVEL = "catalog"

DEFAULT_VIEW = "summary"

# =========================================================
# Temporary Compatibility Wrapper
# =========================================================


class _RowsAdapter:
    """
    Temporary compatibility adapter for
    help.py until it is migrated from
    dataset.rows to raw rows.
    """

    def __init__(
        self,
        rows,
    ):
        self.rows = rows


# =========================================================
# CLI
# =========================================================


@click.command("vars")
@click.argument(
    "args",
    nargs=-1,
)
@click.option(
    "--layer",
    type=click.Choice(
        [
            "schema",
            "metrics",
            "display",
        ],
        case_sensitive=False,
    ),
    help="Filter by ontology layer.",
)
@click.option(
    "--owner",
    type=click.Choice(
        [
            "OWL",
            "ROOST",
        ],
        case_sensitive=False,
    ),
    help="Filter by semantic owner.",
)
@click.option(
    "--domain",
    "semantic_domain",
    type=click.Choice(
        [
            "decision",
            "design",
            "execution",
        ],
        case_sensitive=False,
    ),
    help="Filter by semantic domain.",
)
@click.option(
    "--origin",
    "value_origin",
    type=click.Choice(
        [
            "user-specified",
            "owl-computed",
            "roost-computed",
        ],
        case_sensitive=False,
    ),
    help="Filter by value origin.",
)
@click.option(
    "--projection",
    "projection_kind",
    type=click.Choice(
        [
            "canonical",
            "aggregate",
            "composed",
            "formatted",
            "synthetic",
        ],
        case_sensitive=False,
    ),
    help="Filter by projection kind.",
)
@click.option(
    "--analytic",
    "analytic_kind",
    type=click.Choice(
        [
            "observed",
            "synthetic",
            "comparative",
            "distributional",
            "inferential",
            "aggregate",
        ],
        case_sensitive=False,
    ),
    help="Filter by analytic kind.",
)
@click.option(
    "--materialization",
    "materialization_level",
    type=click.Choice(
        [
            "case",
            "session",
            "run",
            "trial",
        ],
        case_sensitive=False,
    ),
    help="Filter by materialization level.",
)
@click.option(
    "--node",
    "node_type",
    type=click.Choice(
        [
            "variable",
            "overlay",
        ],
        case_sensitive=False,
    ),
    help="Filter by catalog node type.",
)
@click.option(
    "--dashboard",
    type=click.Choice(
        [
            "ontology",
            "inventory",
            "pivot",
        ],
        case_sensitive=False,
    ),
    default="ontology",
    show_default=True,
    help="Catalog dashboard.",
)
@click.option(
    "--view",
    default=DEFAULT_VIEW,
    show_default=True,
    help="Catalog view.",
)
@click.option(
    "--markdown",
    is_flag=True,
)
@click.option(
    "--latex",
    is_flag=True,
)
@click.option(
    "--filter",
    "filters",
    multiple=True,
    help=("Filter rows. Examples: layer=metrics owner=OWL projection_kind=aggregate"),
)
@click.option(
    "--sort",
    type=str,
    help="Sort by field. Prefix '-' for descending.",
)
@click.option(
    "--top",
    type=int,
    help="Limit number of rows.",
)
@click.option(
    "--pivot",
    is_flag=True,
    help="Render transposed layout.",
)
@click.option(
    "--explain",
    type=str,
    help=("Explanation facets. Comma-separated list."),
)
def cmd_vars(
    args,
    layer,
    owner,
    semantic_domain,
    value_origin,
    projection_kind,
    analytic_kind,
    materialization_level,
    node_type,
    dashboard,
    view,
    markdown,
    latex,
    filters,
    sort,
    top,
    pivot,
    explain,
):
    """
    Display ROOST ontology and variable catalog.
    """

    selectors, search_terms = split_catalog_args(
        args,
    )

    # =====================================================
    # Parse explain request
    # =====================================================

    explain_facets, explain_errors = parse_explain_request(
        explain,
    )

    if explain_errors:
        raise click.BadParameter(
            "\n".join(
                explain_errors,
            )
        )

    if explain_facets and not pivot:
        raise click.BadParameter("--explain requires --pivot")

    # =====================================================
    # Registries
    # =====================================================

    schema_registry = build_schema_registry()

    metrics_registry = build_metrics_registry()

    display_registry = build_display_registry(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
    )

    ontology_filters_present = any(
        [
            layer,
            owner,
            semantic_domain,
            value_origin,
            projection_kind,
            analytic_kind,
            materialization_level,
            node_type,
        ]
    )
    show_dashboard = not selectors and not args and not filters and not ontology_filters_present

    # =====================================================
    # Catalog Rows
    # =====================================================

    rows = load_catalog_rows(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
        display_registry=display_registry,
        layer=layer,
        owner=owner,
        semantic_domain=semantic_domain,
        value_origin=value_origin,
        projection_kind=projection_kind,
        analytic_kind=analytic_kind,
        materialization_level=materialization_level,
        node_type=node_type,
        search=search_terms,
    )
    catalog_index = {row["field_name"]: row for row in rows}

    if show_dashboard:
        if dashboard == "ontology":
            render_catalog_ontology_dashboard(
                rows,
            )

        elif dashboard == "pivot":
            render_catalog_pivot_dashboard(
                rows,
            )

        else:
            render_catalog_dashboard(
                rows,
            )

        return

    # =====================================================
    # Help
    # =====================================================

    _x = _RowsAdapter(rows)

    if "help" in (filters or ()):
        render_field_help(
            rows=rows,
            registry=display_registry,
            level=DEFAULT_LEVEL,
            view_name=view,
            mode="view",
            title="Available filter fields",
            examples=[
                "--owner OWL",
                "--domain decision",
                "--projection aggregate",
                "--origin owl-computed",
                "--analytic aggregate",
                "--node overlay",
                "--materialization run",
                "--filter field_name=in:spending,bequest",
            ],
        )

        return

    if "help-all" in (filters or ()):
        render_field_help(
            rows=rows,
            registry=display_registry,
            level=DEFAULT_LEVEL,
            view_name=view,
            mode="all",
            title="All queryable fields",
        )

        return

    # =====================================================
    # Row Pipeline
    # =====================================================

    rows = apply_canonical_sort(
        rows,
    )

    rows = apply_filters(
        rows,
        filters,
    )

    rows = apply_sort(
        rows,
        sort,
    )

    rows = apply_top(
        rows,
        top,
    )

    rows = attach_row_ids(
        rows,
    )

    # =====================================================
    # No Results
    # =====================================================

    if not rows:
        click.echo(
            "No matching variables found.",
        )
        return

    if selectors:
        rows = select_rows_by_id(
            rows,
            selectors,
        )

    # =====================================================
    # Renderer
    # =====================================================

    renderer = resolve_renderer(
        markdown,
        latex,
    )

    # =====================================================
    # Materialize
    # =====================================================

    table = materialize_view(
        rows=rows,
        registry=display_registry,
        catalog_index=catalog_index,
        level=DEFAULT_LEVEL,
        view_name=view,
        mode="pivot" if pivot else "table",
        explain_facets=explain_facets,
    )

    # =====================================================
    # Inject IDs
    # =====================================================

    if not pivot:
        table = inject_id_column(
            table,
            rows,
        )

    # =====================================================
    # Render
    # =====================================================

    output = render_table(
        table,
        renderer,
    )

    if output:
        click.echo(f"viewing: {DEFAULT_LEVEL}/{view}")
        click.echo(
            output,
        )
