# src/owlroost/cli/cmd_vars.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

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
from owlroost.cli.utils import render_table, resolve_renderer, select_rows_by_id, split_catalog_args
from owlroost.display.bootstrap import build_display_registry
from owlroost.display.explain import parse_explain_request
from owlroost.display.materializers.materialize import materialize_view
from owlroost.display.materializers.materialize_dashboard import (
    materialize_dashboard,
)
from owlroost.display.operations.filtering import apply_filters
from owlroost.display.operations.help import render_field_help
from owlroost.display.operations.row_ops import apply_top, attach_row_ids
from owlroost.display.operations.sorting import apply_canonical_sort, apply_sort
from owlroost.display.operations.table_ops import inject_id_column
from owlroost.display.renderers.rich_dashboard import (
    render_rich_dashboard,
)
from owlroost.metrics.bootstrap import build_metrics_registry
from owlroost.schema.bootstrap import build_schema_registry

# =========================================================
# Defaults
# =========================================================

DEFAULT_DASHBOARD = "catalog"

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
@click.pass_context
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
    "--dashboard",
    type=str,
    default=None,
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
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    default=False,
    help="Show all catalog variables.",
)
def cmd_vars(
    ctx,
    args,
    layer,
    dashboard,
    view,
    markdown,
    latex,
    filters,
    sort,
    top,
    pivot,
    explain,
    show_all,
):
    """
    Display ROOST ontology and variable catalog.
    """

    _invoked_as = ctx.info_name
    # set default view to "build" or "cases"
    # will automatically load as "case" view
    if dashboard is None:
        dashboard = ctx.info_name or DEFAULT_DASHBOARD

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

    show_dashboard = not selectors and not args and not filters and not show_all

    # =====================================================
    # Catalog Rows
    # =====================================================

    rows = load_catalog_rows(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
        display_registry=display_registry,
        search=search_terms,
    )
    catalog_index = {row["field_name"]: row for row in rows}

    if show_dashboard:
        dashboard_spec = display_registry.get_dashboard(
            dashboard,
        )

        dashboard_obj = materialize_dashboard(
            dashboard_spec,
            rows=rows,
            registry=display_registry,
            catalog_index=catalog_index,
        )

        render_rich_dashboard(
            dashboard_obj,
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
