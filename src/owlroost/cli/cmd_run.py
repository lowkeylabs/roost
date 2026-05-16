# src/owlroost/cli/cmd_run.py

from __future__ import annotations

import os
from pathlib import Path

import click

from owlroost.cli.utils import (
    prepare_dataset,
    render_table,
    resolve_renderer,
)
from owlroost.core.run_owl_executor import (
    execute_runs,
)
from owlroost.display.bootstrap import (
    build_display_registry,
)
from owlroost.display.loaders import (
    load_runs,
)
from owlroost.display.materialize import (
    apply_derived_metrics,
)
from owlroost.display.utils import (
    inject_id_column,
)
from owlroost.metrics.registry.bootstrap import (
    build_metrics_registry,
)
from owlroost.schema.bootstrap import (
    build_registry,
)
from owlroost.schema.plugins.group_derived import (
    apply_group_derived_metrics,
)

# =========================================================
# CLI
# =========================================================


@click.command("run")
@click.argument(
    "selectors",
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
    help="Filter rows. Examples: case_id=0 trial.pending>0",
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
    "--progress",
    default="rich",
    show_default=True,
    help="Progress renderer: rich, dot, dot2, none",
)
@click.option(
    "--rerun",
    is_flag=True,
    default=False,
    help="Rerun completed trials.",
)
@click.option(
    "--list-only",
    is_flag=True,
    default=False,
    help="Display matching runs but do not execute.",
)
def cmd_run(
    selectors,
    root,
    view,
    markdown,
    latex,
    pivot,
    filters,
    sort,
    top,
    progress,
    rerun,
    list_only,
):
    """
    Display and execute runs.

    Default behavior:

    - discover runs
    - filter to runs with pending trials
    - display matching runs
    - execute pending trials

    Execution uses hybrid scheduling:

    - single-trial runs are bundled
    - multi-trial runs execute independently
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
    # Default Pending Filter
    # =====================================================

    filter_list = list(filters)

    if not rerun:
        filter_list.append("trial.pending>0")

    # =====================================================
    # Dataset Pipeline
    # =====================================================

    ds = prepare_dataset(
        ds,
        selectors=selectors,
        filters=filter_list,
        sort=sort,
        top=top,
    )

    # =====================================================
    # Group Derived Metrics
    # =====================================================

    ds = apply_group_derived_metrics(
        ds,
        use_working_set=(bool(filter_list) or top is not None),
    )

    # =====================================================
    # No Matching Runs
    # =====================================================

    if not ds.rows:
        if rerun:
            click.echo("No matching runs found.")
        else:
            click.echo("No pending runs found.")

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
    # List-only Exit
    # =====================================================

    if list_only:
        return

    # =====================================================
    # Resolve Selected Runs
    # =====================================================

    selected_runs = []

    for row in ds.rows:
        run_dir = row.get("_path")

        if run_dir:
            selected_runs.append(Path(run_dir))

    # =====================================================
    # No Executable Runs
    # =====================================================

    if not selected_runs:
        click.echo("No runs available for execution.")
        return

    # =====================================================
    # Execute
    # =====================================================

    # =====================================================
    # Progress Label Width
    # =====================================================

    labels = []

    for run_dir in selected_runs:
        try:
            run_name = f"{run_dir.parent.parent.parent.name}/{run_dir.name}"
            labels.append(run_name)

        except Exception:
            labels.append(run_dir.name)

    if labels:
        max_label_width = max(len(x) for x in labels)

        os.environ["OWLROOST_PROGRESS_LABEL_WIDTH"] = str(max_label_width)

    click.echo(f"Scheduling {len(selected_runs)} runs.")

    execute_runs(
        selected_runs,
        progress=progress,
        rerun=rerun,
    )


if __name__ == "__main__":
    cmd_run()
