from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from owlroost.domain.metrics.views import TRIAL_VIEW
from owlroost.domain.services.discovery import discover_experiments
from owlroost.domain.services.metrics import build_trial_row
from owlroost.domain.views.inspect import render_run, render_trial

# =========================================================
# Config
# =========================================================

RESULTS_DIR = Path("results")


# =========================================================
# CLI
# =========================================================


@click.command(name="inspect")
@click.argument("level", required=False, type=str)
@click.argument("id", required=False, type=int)
@click.option("--run", "run_id", type=int, help="Select run index")
def cmd_inspect(level: str, id: int | None, run_id: int | None):
    """
    Inspect results using MetricSpec.

    Examples:
        roost inspect trial 0
        roost inspect run
    """
    console = Console()

    # ---------------------------------------------------------
    # Normalize inputs
    # ---------------------------------------------------------

    # Case 1: no args → default to run
    if level is None:
        level = "runs"

    # Case 2: level is actually an integer → treat as run id
    elif level.lstrip("-").isdigit():
        id = int(level)
        level = "runs"

    # Validate level
    if level not in {"runs", "trials"}:
        console.print("[red]Level must be 'runs' or 'trials'[/red]")
        return

    # ---------------------------------------------------------
    # Validate results directory
    # ---------------------------------------------------------
    if not RESULTS_DIR.exists():
        console.print("[red]Results directory not found[/red]")
        return

    experiments = discover_experiments(RESULTS_DIR)

    if not experiments:
        console.print("[yellow]No experiments found[/yellow]")
        return

    # ---------------------------------------------------------
    # Resolve latest experiment + run
    # ---------------------------------------------------------
    exp = experiments[-1]

    if not exp.runs:
        console.print("[yellow]No runs found in latest experiment[/yellow]")
        return

    # Normalize run_id (support negative indexing)
    num_runs = len(exp.runs)

    if run_id is None:
        run_index = num_runs - 1
    else:
        # convert negative index
        if run_id < 0:
            run_index = num_runs + run_id
        else:
            run_index = run_id

        # validate final index
        if run_index < 0 or run_index >= num_runs:
            console.print(
                f"[red]Invalid run id: {run_index}[/red] (valid range: {-num_runs} to {num_runs-1})"
            )
            return

    run = exp.runs[run_index]

    # ---------------------------------------------------------
    # RUN LEVEL
    # ---------------------------------------------------------
    if level == "runs":
        num_runs = len(exp.runs)

        # -----------------------------------------
        # List all runs
        # -----------------------------------------
        if id is None:
            console.print("\n[bold]Runs (latest experiment)[/bold]\n")

            for i, r in enumerate(exp.runs):
                console.print(f"[cyan]{i}[/cyan]  trials={len(r.trials)}  {r.path}")

            return

        # -----------------------------------------
        # Resolve run index (support negative)
        # -----------------------------------------
        if id < 0:
            run_index = num_runs + id
        else:
            run_index = id

        if run_index < 0 or run_index >= num_runs:
            console.print(f"[red]Invalid run id[/red] (valid range: {-num_runs} to {num_runs-1})")
            return

        run = exp.runs[run_index]

        # -----------------------------------------
        # Show run detail (no trials yet)
        # -----------------------------------------
        console.print(f"\n[bold]Run {run_index}[/bold]")
        console.print(f"[dim]{run.path}[/dim]\n")
        console.print(f"Trials: {len(run.trials)}")

        return

    # ---------------------------------------------------------
    # TRIAL LEVEL
    # ---------------------------------------------------------
    if level == "trials":
        # -----------------------------------------
        # List all trials
        # -----------------------------------------
        if id is None:
            rows = []

            for trial in run.trials:
                row = build_trial_row(trial.path, TRIAL_VIEW)
                if row:
                    rows.append(row)

            if not rows:
                console.print("[yellow]No metrics found[/yellow]")
                return

            console.print(f"\n[bold]Trials for Run {run_index}[/bold]")
            console.print(f"[dim]{run.path}[/dim]\n")

            render_run(console, rows, TRIAL_VIEW)
            return

        # -----------------------------------------
        # Single trial
        # -----------------------------------------
        if id < 0 or id >= len(run.trials):
            console.print("[red]Invalid trial id[/red]")
            return

        trial = run.trials[id]

        row = build_trial_row(trial.path, TRIAL_VIEW)

        if not row:
            console.print("[red]No _metrics.json found[/red]")
            return

        console.print(f"\n[bold]Trial {id} (Run {run_index})[/bold]")
        console.print(f"[dim]{trial.path}[/dim]\n")

        render_trial(console, row, TRIAL_VIEW)
        return
