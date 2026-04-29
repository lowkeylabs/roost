from __future__ import annotations

import sys
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.table import Table

from owlroost.cli.utils import open_in_file_explorer
from owlroost.domain.formatting import format_value
from owlroost.domain.registry import COLUMN_REGISTRY, VIEW_REGISTRY
from owlroost.domain.services.discovery import discover_experiments
from owlroost.domain.services.experiments import build_experiment_rows
from owlroost.domain.services.trials import build_trial_rows
from owlroost.domain.views.analysis_registry import ANALYSIS_VIEW_REGISTRY
from owlroost.domain.views.table import build_rows

RESULTS_DIR = Path("results")
WORKFLOW_NAME = "audit"

# =========================================================
# CLI
# =========================================================


@click.command(name="audit")
@click.argument("experiment_id", required=False, type=int)
@click.option("--view", default="dashboard")
@click.option("--run", "run_id", type=int)
@click.option("--export", "export_id", type=int)
@click.option("--open-folder", "open_id", type=int)
def cmd_audit(experiment_id, view, run_id, export_id, open_id):
    console = Console()

    # ---------------------------------------------------------
    # Validate actions
    # ---------------------------------------------------------
    actions = [run_id, export_id, open_id]
    if sum(x is not None for x in actions) > 1:
        console.print("[red]Use only one of --run, --export, or --open-folder[/red]")
        sys.exit(1)

    if not RESULTS_DIR.exists():
        console.print("[red]Results directory not found.[/red]")
        sys.exit(1)

    experiments = discover_experiments(RESULTS_DIR)

    if not experiments:
        console.print("[yellow]No experiments found.[/yellow]")
        return

    # ---------------------------------------------------------
    # Validate / route view
    # ---------------------------------------------------------

    # Analysis view (failures, etc.)
    if view in ANALYSIS_VIEW_REGISTRY:
        if experiment_id is None or len(experiments) != 1:
            console.print("[red]Analysis views require exactly one experiment ID[/red]")
            return

        trial_rows = build_trial_rows([experiments[0]])
        ANALYSIS_VIEW_REGISTRY[view](trial_rows)
        return

    # Table view
    view_key = WORKFLOW_NAME + "_" + view

    if view_key not in VIEW_REGISTRY:
        available = ", ".join(
            [v.replace(WORKFLOW_NAME + "_", "") for v in VIEW_REGISTRY.keys()]
            + list(ANALYSIS_VIEW_REGISTRY.keys())
        )
        console.print(f"[red]Unknown view '{view}'. Available: {available}[/red]")
        return

    # ---------------------------------------------------------
    # Single experiment detail
    # ---------------------------------------------------------
    if experiment_id is not None:
        if experiment_id < 0 or experiment_id >= len(experiments):
            console.print("[red]Invalid experiment ID.[/red]")
            sys.exit(1)

        experiments = [experiments[experiment_id]]

    # ---------------------------------------------------------
    # Build rows
    # ---------------------------------------------------------
    experiment_rows = build_experiment_rows(experiments)

    column_keys = VIEW_REGISTRY[view_key]
    rows = build_rows(experiment_rows, column_keys)

    # ---------------------------------------------------------
    # Handle actions (trial-level)
    # ---------------------------------------------------------
    if run_id is not None or export_id is not None or open_id is not None:
        trial_rows = build_trial_rows(experiments)
        runtime_rows = [
            {"runtime": r.runtime, "path": r.path} for r in trial_rows if r.runtime is not None
        ]

        if not runtime_rows:
            console.print("[yellow]No runtime data available.[/yellow]")
            return

        runtime_rows = sorted(runtime_rows, key=lambda r: r["runtime"], reverse=True)

        action_id = (
            run_id if run_id is not None else export_id if export_id is not None else open_id
        )
        action_type = "run" if run_id is not None else "export" if export_id is not None else "open"

        if action_id < 0 or action_id >= len(runtime_rows):
            console.print("[red]Invalid ID[/red]")
            return

        trial_path = runtime_rows[action_id]["path"]

        if action_type == "open":
            open_in_file_explorer(trial_path)
            console.print(f"[cyan]Opened folder:[/cyan] {trial_path}")

        elif action_type == "run":
            rerun_trial(console, trial_path)

        elif action_type == "export":
            export_trial(console, trial_path)

        return

    # ---------------------------------------------------------
    # Render table (registry-driven)
    # ---------------------------------------------------------
    table = Table(
        header_style="bold cyan",
        row_styles=["none", "none"],
        box=box.SIMPLE,
        show_header=True,
        show_edge=False,
        show_lines=False,
    )

    table.add_column("ID", justify="right")

    for key in column_keys:
        col = COLUMN_REGISTRY[key]
        table.add_column(col.label, justify=col.align)

    for idx, row in enumerate(rows):
        formatted_row = [str(idx)]

        for key in column_keys:
            col = COLUMN_REGISTRY[key]
            formatted = format_value(row[key], col.fmt)
            formatted_row.append(formatted)

        table.add_row(*formatted_row)

    console.print(table)


# =========================================================
# Actions (unchanged)
# =========================================================


def rerun_trial(console, trial_path: Path):
    import os
    import time
    from contextlib import contextmanager

    import owlplanner as owl

    from owlroost.core.metrics_from_plan import write_metrics_json

    @contextmanager
    def chdir(path: Path):
        old = Path.cwd()
        try:
            os.chdir(path)
            yield
        finally:
            os.chdir(old)

    toml = next(trial_path.glob("*_effective.toml"), None)

    if not toml:
        console.print("[red]No _effective.toml found[/red]")
        return

    console.print(f"[bold cyan]Re-running[/bold cyan] {trial_path}")

    with chdir(trial_path):
        try:
            plan = owl.readConfig(toml.name, logstreams="loguru", loadHFP=True)

            start = time.time()
            plan.solve(plan.objective, dict(plan.solverOptions))
            elapsed = time.time() - start

            console.print(f"[cyan]Status:[/cyan] {plan.caseStatus}")
            console.print(f"[yellow]Time:[/yellow] {elapsed:.3f}s")

            if plan.caseStatus != "solved":
                return

            base = Path(toml.stem)

            plan.saveWorkbook(
                basename=(base.stem + "_results.xlsx"),
                overwrite=True,
                with_config="no",
            )

            write_metrics_json(
                plan,
                base.with_name(base.stem + "_metrics.json"),
                {"elapsed_seconds": elapsed},
            )

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


def export_trial(console, trial_path: Path):
    import zipfile

    safe_name = "__".join(trial_path.parts)
    zip_path = Path("exports") / f"export__{safe_name}.zip"
    zip_path.parent.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in trial_path.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(trial_path))

    console.print(f"[green]Exported:[/green] {zip_path}")
