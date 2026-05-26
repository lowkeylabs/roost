# src/owlroost/cli/cmd_vars.py

from __future__ import annotations

import click

from owlroost.catalog.loaders import (
    load_catalog_dataset,
)
from owlroost.cli.utils import (
    prepare_dataset,
    render_table,
    resolve_renderer,
)
from owlroost.display.bootstrap import (
    build_display_registry,
)
from owlroost.display.utils import (
    attach_row_ids,
    inject_id_column,
    render_field_help,
)
from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)
from owlroost.schema.bootstrap import (
    build_registry,
)

# =========================================================
# CLI
# =========================================================


@click.command("vars")
@click.argument(
    "query",
    required=False,
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
    "--view",
    default="summary",
    show_default=True,
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
    help=("Filter rows. " "Examples: " "layer=schema " "source=_metrics"),
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
def cmd_vars(
    query,
    layer,
    view,
    markdown,
    latex,
    filters,
    sort,
    top,
):
    """
    Display ROOST variable catalog.

    Examples:

      roost vars

      roost vars spending

      roost vars --layer metrics

      roost vars --view provenance

      roost vars --filter layer=metrics

      roost vars --sort field_name
    """

    # =====================================================
    # Build Registries
    # =====================================================

    schema_registry = build_registry()

    metrics_registry = build_metrics_registry()

    display_registry = build_display_registry(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
    )

    # =====================================================
    # Load Catalog Dataset
    # =====================================================

    ds = load_catalog_dataset(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
        display_registry=display_registry,
        layer=layer,
        search=query,
    )

    # =====================================================
    # Add Row IDs
    # =====================================================

    ds = attach_row_ids(
        ds,
    )

    # =====================================================
    # Context-sensitive help
    # =====================================================

    if "help" in (filters or ()):
        render_field_help(
            dataset=ds,
            registry=display_registry,
            level="catalog",
            view_name=view,
            mode="view",
            title="Available filter fields",
            examples=[
                "--filter layer=schema",
                "--filter source=_metrics",
                "--filter field_name=in:spending,bequest",
            ],
        )

        return

    if "help-all" in (filters or ()):
        render_field_help(
            dataset=ds,
            registry=display_registry,
            level="catalog",
            view_name=view,
            mode="all",
            title="All queryable fields",
        )

        return

    # =====================================================
    # Dataset Pipeline
    # =====================================================

    ds = prepare_dataset(
        ds,
        selectors=[],
        filters=filters,
        sort=sort,
        top=top,
    )

    # =====================================================
    # No Results
    # =====================================================

    if not ds.rows:
        click.echo("No matching variables found.")
        return

    # =====================================================
    # Resolve Renderer
    # =====================================================

    renderer = resolve_renderer(
        markdown,
        latex,
    )

    # =====================================================
    # Materialize View
    # =====================================================

    table = ds.view(
        registry=display_registry,
        name=view,
        layout="table",
    )

    # =====================================================
    # Inject Row IDs
    # =====================================================

    table = inject_id_column(
        table,
        ds,
    )

    # =====================================================
    # Render
    # =====================================================

    output = render_table(
        table,
        renderer,
    )

    if output:
        click.echo(
            output,
        )
