# src/owlroost/cli/cmd_results.py

from __future__ import annotations

import click

from owlroost.display.bootstrap import build_display_registry
from owlroost.display.loaders import load_runs
from owlroost.display.materialize import apply_derived_metrics
from owlroost.display.renderers.latex_table import render_latex_table
from owlroost.display.renderers.markdown_table import render_markdown_table
from owlroost.display.renderers.rich_table import render_rich_table
from owlroost.display.utils import attach_row_ids, inject_id_column
from owlroost.metrics.registry.bootstrap import build_metrics_registry
from owlroost.schema.bootstrap import build_registry

# =========================================================
# Renderer Helpers
# =========================================================


def render_table(
    table,
    renderer,
):
    """
    Dispatch table renderer.
    """

    if renderer == "markdown":
        return render_markdown_table(table)

    if renderer == "latex":
        return render_latex_table(table)

    return render_rich_table(table)


def resolve_renderer(
    markdown=False,
    latex=False,
):
    """
    Resolve renderer name from CLI flags.
    """

    if markdown:
        return "markdown"

    if latex:
        return "latex"

    return "rich"


# =========================================================
# CLI
# =========================================================


@click.command("results")
@click.option(
    "--view",
    default="results",
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
    "--pivot",
    is_flag=True,
)
@click.option(
    "--filter",
    "filters",
    multiple=True,
    help=("Filter rows. " "Examples: case_id=0 " "trial.completed>50"),
)
@click.option(
    "--sort",
    type=str,
    help=("Sort by field. " "Prefix '-' for descending."),
)
@click.option(
    "--top",
    type=int,
    help="Limit number of rows.",
)
def cmd_results(
    view,
    markdown,
    latex,
    pivot,
    filters,
    sort,
    top,
):
    """
    Display discovered runs from ./results.

    Examples:

      roost results

      roost results --view basic

      roost results --pivot

      roost results --filter case_id=0

      roost results --sort -trial.completed

      roost results --top 10
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
    # Discover + Load Runs
    # =====================================================

    ds = load_runs(
        metrics_registry=metrics_registry,
        results_root="results",
    )

    if not ds.rows:
        click.echo("No runs found.")
        return

    # =====================================================
    # Derived Metrics
    # =====================================================

    for row in ds.rows:
        apply_derived_metrics(
            row,
            display_registry,
        )

    # =====================================================
    # Dataset Pipeline
    # =====================================================

    ds = ds.canonical_sort()

    ds = attach_row_ids(ds)

    ds = ds.filter(*filters)

    ds = ds.sort(sort)

    ds = ds.top(top)

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
        level="run",
        name=view,
        layout="pivot" if pivot else "table",
    )

    # =====================================================
    # Add Row IDs
    # =====================================================

    if not pivot:
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
        click.echo(output)
