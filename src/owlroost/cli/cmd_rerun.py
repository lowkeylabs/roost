# src/owlroost/cli/cmd_rerun.py

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click
from loguru import logger
from rich.console import Console

# reuse helper from inspect
from owlroost.cli.cmd_inspect import runrow_to_dict
from owlroost.core.progress_renderers import create_renderer
from owlroost.domain.metrics.view_registry import get_view
from owlroost.domain.services.discovery import discover_experiments
from owlroost.domain.services.query import apply_filters, apply_sort, apply_top
from owlroost.domain.services.rows import build_run_rows
from owlroost.domain.views.inspect import render_table

RESULTS_DIR = Path("results")


# =========================================================
# Trial selection
# =========================================================


def trial_id_str(t) -> str:
    """Canonical trial id from folder name (e.g., '0007')."""
    try:
        return Path(t.path).name
    except Exception:
        return "????"


def get_failure_category(t):
    # --------------------------------------------------
    # Try cached data first
    # --------------------------------------------------
    data = t.data or {}

    if data:
        fc = data.get("run_status", {}).get("failure_category")
        if fc:
            return fc.lower()

    # --------------------------------------------------
    # Fallback: load metrics.json directly
    # --------------------------------------------------
    trial_path = Path(t.path)
    metrics_files = list(trial_path.glob("*_metrics.json"))

    if metrics_files:
        try:
            with open(metrics_files[0]) as f:
                data = json.load(f)
                fc = data.get("run_status", {}).get("failure_category")
                if fc:
                    return fc.lower()
        except Exception:
            pass

    return ""


def find_trials(run, include_all_failures=False, debug=False):
    selected = []

    for t in run.trials:
        status = (t.status or "").lower()
        failure = get_failure_category(t)

        if debug:
            trial_id = Path(t.path).name
            print(f"Trial {trial_id} | status={status:<12} | failure={failure or '-'}")

        is_timeout = "timeout" in failure or status == "timeout"

        is_failed = status in {"failed", "unsuccessful", "crashed", "timeout"}

        if is_timeout:
            selected.append(t)
        elif include_all_failures and is_failed:
            selected.append(t)

    if debug:
        print(f"\nSelected {len(selected)} / {len(run.trials)} trials\n")

    return selected


# =========================================================
# Subprocess execution
# =========================================================


def run_trial_subprocess(trial, timeout):
    trial_path = Path(trial.path)

    # --------------------------------------------------
    # Clean old artifacts (CRITICAL)
    # --------------------------------------------------
    for pattern in [
        "*_metrics.json",
        "*_results.xlsx",
        "*_summary.json",
        "*_rates.xlsx",
        "FAILED",
        "TIMEOUT",
        "SOLVED",
    ]:
        for f in trial_path.glob(pattern):
            f.unlink(missing_ok=True)

    toml_files = list(trial_path.glob("*_effective.toml"))
    if not toml_files:
        logger.warning(f"No effective TOML in {trial_path}")
        return False

    toml_file = toml_files[0]

    existing = list(trial_path.glob("*_results.xlsx"))

    if existing:
        output_file = str(existing[0])
    else:
        output_file = str(trial_path / f"{trial_path.name}_results.xlsx")

    args = {
        "case_file": str(toml_file),
        "overrides": {},
        "output_file": output_file,
        "roost_runtime": {"worker_timeout": timeout},
        "longevity_runtime": None,
    }

    try:
        result = subprocess.run(
            [sys.executable, "-m", "owlroost.entrypoints.run_case"],
            input=json.dumps(args),
            text=True,
            capture_output=True,
            timeout=timeout + 5,
        )
    except subprocess.TimeoutExpired:
        logger.warning(f"Trial {trial.id} timed out again")
        return False

    if result.returncode != 0:
        logger.error(f"Trial {trial.id} crashed: {result.stderr}")
        return False

    try:
        data = json.loads(result.stdout)
    except Exception:
        logger.error(f"Trial {trial.id} invalid JSON")
        return False

    trial_path.joinpath("FAILED").unlink(missing_ok=True)
    trial_path.joinpath("TIMEOUT").unlink(missing_ok=True)

    status = (data.get("status") or "").upper()
    trial_path.joinpath(status).touch(exist_ok=True)

    return True


# =========================================================
# CLI
# =========================================================


@click.command(name="rerun")
@click.argument("run_id", required=False, type=int)
@click.option("--timeout", default=60)
@click.option("--jobs", default=4)
@click.option("--all-failures", is_flag=True)
@click.option("--execute", is_flag=True)
@click.option("--view", default="audit")
@click.option("--sort", type=str)
@click.option("--top", type=int)
@click.option("--filter", "filters", multiple=True)
@click.option("--pivot", is_flag=True, default=None)
def cmd_rerun(
    run_id,
    timeout,
    jobs,
    all_failures,
    execute,
    view,
    sort,
    top,
    filters,
    pivot,
):
    console = Console()

    if not RESULTS_DIR.exists():
        console.print("[red]Results directory not found[/red]")
        return

    experiments = discover_experiments(RESULTS_DIR)
    run_rows = build_run_rows(experiments)

    # =========================================================
    # DISCOVERY MODE
    # =========================================================
    if run_id is None:
        console.print("[bold]Runs (rerun candidates)[/bold]\n")

        # convert rows
        working_rows = [runrow_to_dict(r) for r in run_rows]

        # resolve view
        selected_view, layout, _ = get_view("run", view)

        if pivot is True:
            layout = "pivot"

        # apply query pipeline
        working_rows = apply_filters(working_rows, selected_view, filters)
        working_rows = apply_sort(working_rows, selected_view, sort)
        working_rows = apply_top(working_rows, top)

        render_table(console, working_rows, selected_view, layout=layout)

        console.print("\n[yellow]Select a run_id to rerun[/yellow]")
        console.print("Example: roost rerun 3 --execute --timeout 60")
        return

    # =========================================================
    # TARGETED RUN
    # =========================================================
    runs = []
    for exp in experiments:
        for run in exp.runs:
            runs.append(run)

    if run_id < 0 or run_id >= len(runs):
        console.print("[red]Invalid run id[/red]")
        return

    run = runs[run_id]

    console.print(f"[bold]Rerun analysis for run {run_id}[/bold]")
    console.print(f"[dim]{run.path}[/dim]\n")

    trials = find_trials(run, include_all_failures=all_failures)

    if not trials:
        console.print("[green]No trials require rerun[/green]")
        return

    console.print(f"[cyan]Trials identified: {len(trials)}[/cyan]\n")

    for t in trials:
        trial_id = Path(t.path).name
        failure = get_failure_category(t)

        console.print(f"  Trial {trial_id} | {failure or '-'}")

    console.print()

    if not execute:
        console.print("[yellow]Dry run only. Use --execute to rerun.[/yellow]")
        return

    # =========================================================
    # EXECUTION
    # =========================================================
    renderer = create_renderer("rich", console, "Rerunning trials")
    renderer.start(len(trials))

    completed = 0
    success = 0

    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {executor.submit(run_trial_subprocess, t, timeout): t for t in trials}

        for future in as_completed(futures):
            t = futures[future]

            try:
                ok = future.result()
                if ok:
                    success += 1
            except Exception:
                pass

            completed += 1
            renderer.advance(1, completed, len(trials))

    renderer.finish()

    console.print(f"\n[bold]Rerun complete:[/bold] {success}/{len(trials)} succeeded")
