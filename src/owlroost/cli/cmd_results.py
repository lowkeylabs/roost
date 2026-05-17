# src/owlroost/cli/cmd_results.py

from __future__ import annotations

import click

from owlroost.cli.utils import (
    prepare_dataset,
    render_table,
    resolve_renderer,
    split_build_args,
)
from owlroost.display.bootstrap import build_display_registry
from owlroost.display.compare import materialize_compare_table
from owlroost.display.loaders import load_runs
from owlroost.display.materialize import apply_derived_metrics
from owlroost.display.utils import (
    attach_row_ids,
    inject_id_column,
    render_field_help,
)
from owlroost.metrics.registry.bootstrap import build_metrics_registry
from owlroost.schema.bootstrap import build_registry
from owlroost.schema.plugins.group_derived import (
    apply_group_derived_metrics,
)

# =========================================================
# CLI
# =========================================================


@click.command("results")
@click.argument(
    "args",
    nargs=-1,
)
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
    help="Render transposed pivot layout.",
)
@click.option(
    "--compare",
    is_flag=True,
    help="Structural side-by-side comparison.",
)
@click.option(
    "--diff",
    is_flag=True,
    help="Show only differing structural fields.",
)
@click.option(
    "--explain",
    type=str,
    help=(
        "Explanation facets. " "Comma-separated list from: " "variables,values,sources,debug,all"
    ),
)
@click.option(
    "--filter",
    "filters",
    multiple=True,
    help=("Filter rows. " "Examples: " "trial.completed>50 " "metrics.success_rate>0.9"),
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
def cmd_results(
    args,
    view,
    markdown,
    latex,
    pivot,
    compare,
    diff,
    explain,
    filters,
    sort,
    top,
):
    """
    Display discovered runs from ./results.

    Examples:

      roost results

      roost results 0

      roost results 0,1,2

      roost results --view basic

      roost results --pivot

      roost results --compare

      roost results --diff

      roost results --filter case_id=0

      roost results --sort -trial.completed

      roost results --top 10

      roost results 0 --explain=all
    """

    # =====================================================
    # Parse CLI args
    # =====================================================

    selectors, overrides = split_build_args(args)

    if overrides:
        raise click.ClickException("Hydra-style overrides are not supported in " "'roost results'.")

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

    ds = attach_row_ids(ds)

    # =====================================================
    # Context-sensitive CLI help
    # =====================================================

    if "help" in (filters or ()):
        render_field_help(
            dataset=ds,
            registry=display_registry,
            level="run",
            view_name=view,
            mode="view",
            title="Available filter fields",
            examples=[
                "--filter id=in:1,2,3",
                "--filter trial.completed>50",
                "--filter metrics.success_rate>0.9",
                "--filter status=success",
            ],
        )

        return

    if "help-all" in (filters or ()):
        render_field_help(
            dataset=ds,
            registry=display_registry,
            level="run",
            view_name=view,
            mode="all",
            title="All queryable fields",
        )

        return

    if sort == "help":
        render_field_help(
            dataset=ds,
            registry=display_registry,
            level="run",
            view_name=view,
            mode="view",
            title="Available sort fields",
            examples=[
                "--sort throughput",
                "--sort -throughput",
                "--sort elapsed",
            ],
        )

        return

    if sort == "help-all":
        render_field_help(
            dataset=ds,
            registry=display_registry,
            level="run",
            view_name=view,
            mode="all",
            title="All queryable fields",
            examples=[
                "--sort throughput",
                "--sort -throughput",
                "--sort elapsed",
            ],
        )

        return

    if str(top).lower() == "help":
        click.echo()
        click.echo("Limit displayed rows.")
        click.echo()
        click.echo("Examples:")
        click.echo()
        click.echo("  --top 5")
        click.echo("  --top 10")
        click.echo()

        return

    # =====================================================
    # No Results
    # =====================================================

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

    ds = prepare_dataset(
        ds,
        selectors=selectors,
        filters=filters,
        sort=sort,
        top=top,
    )

    ds = apply_group_derived_metrics(
        ds,
        use_working_set=(bool(filters) or top is not None),
    )

    if not ds.rows:
        click.echo("No matching runs found.")
        return

    # =====================================================
    # Resolve Renderer
    # =====================================================

    renderer = resolve_renderer(
        markdown,
        latex,
    )

    # =====================================================
    # Normalize explain facets
    # =====================================================

    explain_facets = set()

    if explain:
        explain_facets = {x.strip() for x in explain.split(",") if x.strip()}

        if "all" in explain_facets:
            explain_facets = {
                "variables",
                "values",
                "sources",
                "debug",
            }

    # =====================================================
    # Structural compare/diff mode
    # =====================================================

    if compare or diff:
        table = materialize_compare_table(
            dataset=ds,
            diff_only=diff,
            explain=explain_facets,
        )

        output = render_table(
            table,
            renderer,
        )

        if output:
            click.echo(output)

        return

    # =====================================================
    # Materialize View
    # =====================================================

    table = ds.view(
        registry=display_registry,
        level="run",
        name=view,
        layout="pivot" if pivot else "table",
        explain=explain_facets,
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
