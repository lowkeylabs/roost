# src/owlroost/cli/cmd_run.py

from __future__ import annotations

from pathlib import Path

import click

from owlroost.core.run_owl_executor import (
    execute_runs,
    index_runs,
    render_run_summary,
    resolve_run_selection,
)
from owlroost.display.discovery import (
    find_all_runs,
)


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
    "--progress",
    default="rich",
    show_default=True,
    help=("Progress renderer: " "rich, dot, dot2, none"),
)
def cmd_run(
    run_ids,
    root,
    progress,
):
    """
    List runs and execute pending trials.

    Examples:
      roost run
      roost run 0
      roost run 0 1 2
    """

    root = Path(root).resolve()

    # ----------------------------------------
    # Discover runs
    # ----------------------------------------
    runs = find_all_runs(root)

    if not runs:
        click.echo("No runs found.")

        return

    indexed_runs = index_runs(runs)

    # ----------------------------------------
    # No args -> LIST
    # ----------------------------------------
    if not run_ids:
        render_run_summary(
            indexed_runs,
            root,
        )

        return

    # ----------------------------------------
    # Resolve selected runs
    # ----------------------------------------
    selected_runs = resolve_run_selection(
        run_ids,
        indexed_runs,
    )

    click.echo()

    click.echo(f"Executing " f"{len(selected_runs)} runs.")

    # ----------------------------------------
    # Execute runs sequentially
    # ----------------------------------------
    execute_runs(
        selected_runs,
        progress=progress,
    )


if __name__ == "__main__":
    cmd_run()
