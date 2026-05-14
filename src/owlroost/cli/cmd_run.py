# src/owlroost/cli/cmd_run.py

from __future__ import annotations

from pathlib import Path

import click

from owlroost.core.run_owl_executor import execute_runs
from owlroost.display.bootstrap import build_display_registry
from owlroost.display.loaders import load_runs
from owlroost.display.materialize import apply_derived_metrics
from owlroost.display.renderers.latex_table import render_latex_table
from owlroost.display.renderers.markdown_table import render_markdown_table
from owlroost.display.renderers.rich_table import render_rich_table
from owlroost.display.utils import (
    attach_row_ids,
    inject_id_column,
)
from owlroost.metrics.registry.bootstrap import (
    build_metrics_registry,
)
from owlroost.schema.bootstrap import build_registry
from owlroost.schema.plugins.group_derived import (
    apply_group_derived_metrics,
)

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


@click.command("run")
@click.argument(
    "run_ids",
    nargs=-1,
)
@click.option(
    "--root",
    default="results",
    type=click.Path(exists=True),
)
@click.option(
    "--view",
    default="run",
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
@click.option(
    "--progress",
    default="rich",
    show_default=True,
    help="Progress renderer: rich, dot, dot2, none",
)
@click.option(
    "--rerun",
    is_flag=True,
    default=False,
)
@click.option(
    "--run-all",
    is_flag=True,
    default=False,
    help="Execute all runs in the current working dataset.",
)
def cmd_run(
    run_ids, root, view, markdown, latex, pivot, filters, sort, top, progress, rerun, run_all
):
    """
    List runs and execute pending trials.

    Examples:

      roost run

      roost run 0

      roost run 0 1 2

      roost run --filter success_rate<0.9

      roost run --sort -throughput

      roost run --top 5
    """

    root = Path(root).resolve()

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
        results_root=str(root),
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
    # Group Derived Metrics
    # =====================================================

    apply_group_derived_metrics(
        ds,
        use_working_set=(bool(filters) or top is not None),
    )

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
    # Render Table
    # =====================================================

    output = render_table(
        table,
        renderer,
    )

    if output:
        click.echo(output)

    # =====================================================
    # No selection -> display only
    # =====================================================

    if not run_ids and not run_all:
        return

    # =====================================================
    # Resolve selected runs from displayed dataset
    # =====================================================

    if run_all:
        selected_rows = ds.rows

    else:
        selected_rows = []

        row_id_set = {str(rid) for rid in run_ids}

        for row in ds.rows:
            row_id = str(row.get("_row_id", {}))
            if row_id in row_id_set:
                selected_rows.append(row)

    if not selected_rows:
        raise click.ClickException("No matching run IDs selected.")

    # =====================================================
    # Extract run directories
    # =====================================================

    selected_runs = []

    for row in selected_rows:
        run_dir = row.get("_path")
        if run_dir:
            selected_runs.append(Path(run_dir))

    # =====================================================
    # Execute
    # =====================================================

    click.echo()

    click.echo(f"Executing {len(selected_runs)} runs.")

    execute_runs(
        selected_runs,
        progress=progress,
        rerun=rerun,
    )


if __name__ == "__main__":
    cmd_run()
