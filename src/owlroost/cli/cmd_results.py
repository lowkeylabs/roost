# src/owlroost/cli/cmd_results.py

from __future__ import annotations

import click

from owlroost.cli.utils import prepare_dataset, render_table, resolve_renderer
from owlroost.display.bootstrap import build_display_registry
from owlroost.display.loaders import load_runs
from owlroost.display.materialize import apply_derived_metrics
from owlroost.display.utils import inject_id_column, render_field_help
from owlroost.metrics.registry.bootstrap import build_metrics_registry
from owlroost.schema.bootstrap import build_registry
from owlroost.schema.plugins.group_derived import (
    apply_group_derived_metrics,
)

# =========================================================
# CLI
# =========================================================


@click.command("results")
@click.argument("selectors", nargs=-1)
@click.option("--view", default="results", show_default=True)
@click.option("--markdown", is_flag=True)
@click.option("--latex", is_flag=True)
@click.option("--pivot", is_flag=True)
@click.option(
    "--filter", "filters", multiple=True, help="Filter rows. Examples: case_id=0 trial.completed>50"
)
@click.option("--sort", type=str, help="Sort by field. Prefix '-' for descending.")
@click.option("--top", type=int, help="Limit number of rows.")
def cmd_results(
    selectors,
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
    # Context-sensitive CLI help
    # =====================================================

    if "help" in (filters or ()):
        render_field_help(
            display_registry,
            title="Available filter fields",
            examples=[
                "--filter display.total_savings>2000000",
                "--filter optimization_parameters.objective=maxBequest",
                "--filter rates_selection.method=user",
            ],
        )

        return

    if sort == "help":
        render_field_help(
            display_registry,
            title="Available sort fields",
            examples=[
                "--sort display.total_savings",
                "--sort -display.total_savings",
                "--sort display.fixed_income",
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
