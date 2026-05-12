# src/owlroost/cli/cmd_results.py

from __future__ import annotations

import click

from owlroost.display.bootstrap import (
    build_display_registry,
)
from owlroost.display.loaders import (
    load_runs,
)
from owlroost.display.materialize import (
    materialize_view,
)
from owlroost.display.renderers.latex_table import (
    render_latex_table,
)
from owlroost.display.renderers.markdown_table import (
    render_markdown_table,
)
from owlroost.display.renderers.rich_table import (
    render_rich_table,
)
from owlroost.display.utils import (
    attach_row_ids,
    inject_id_column,
)
from owlroost.metrics.registry.bootstrap import (
    build_metrics_registry,
)
from owlroost.schema.bootstrap import (
    build_registry,
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


@click.command("results")
@click.option(
    "--view",
    default="basic",
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
def cmd_results(
    view,
    markdown,
    latex,
):
    """
    Display discovered runs from ./results.

    Examples:
      roost results
      roost results --view basic
      roost results --markdown
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

    ds = attach_row_ids(
        load_runs(
            metrics_registry=metrics_registry,
            results_root="results",
        )
    )

    if not ds.rows:
        click.echo("No runs found.")

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

    table = materialize_view(
        dataset=ds,
        registry=display_registry,
        level="run",
        view_name=view,
        mode="table",
    )

    # =====================================================
    # Add Row IDs
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
        click.echo(output)
