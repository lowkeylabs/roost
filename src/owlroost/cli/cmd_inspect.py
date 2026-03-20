from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from owlroost.domain.metrics.views import RUN_VIEW, TRIAL_VIEW
from owlroost.domain.services.aggregation import aggregate_rows
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
@click.option("--sort", "sort_key", type=str, help="Sort by metric key (prefix + or -)")
@click.option("--top", "top_n", type=int, help="Limit to top N rows")
@click.option(
    "--filter",
    "filters",
    multiple=True,
    help="Filter rows: key=value (can repeat)",
)
def cmd_inspect(
    level: str,
    id: int | None,
    run_id: int | None,
    sort_key: str | None,
    top_n: int | None,
    filters: list[str],
):
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
        # Aggregate trials to runs
        # -----------------------------------------
        run_rows = []

        for i, r in enumerate(exp.runs):
            trial_rows = []

            for trial in r.trials:
                row = build_trial_row(trial.path, TRIAL_VIEW)
                if row:
                    trial_rows.append(row)

            if not trial_rows:
                continue

            summary = aggregate_rows(trial_rows, TRIAL_VIEW)

            # include run index for display
            summary["run_id"] = i
            summary["trial_count"] = len(trial_rows)

            run_rows.append(summary)

        if not run_rows:
            console.print("[yellow]No metrics found[/yellow]")
            return

        console.print("\n[bold]Runs (latest experiment)[/bold]\n")

        render_run(console, run_rows, RUN_VIEW)

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

            # -----------------------------------------
            # FILTER
            # -----------------------------------------
            try:
                rows = apply_filters(rows, TRIAL_VIEW, filters)
            except ValueError as e:
                console.print(f"[red]{e}[/red]")
                return

            # -----------------------------------------
            # SORT
            # -----------------------------------------
            try:
                rows = apply_sort(rows, TRIAL_VIEW, sort_key)
            except ValueError as e:
                console.print(f"[red]{e}[/red]")
                return

            # -----------------------------------------
            # TOP
            # -----------------------------------------
            rows = apply_top(rows, top_n)

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


def apply_sort(rows: list[dict], specs: list, sort_key: str):
    if not sort_key:
        return rows

    direction = -1
    key = sort_key

    if sort_key.startswith("+"):
        direction = 1
        key = sort_key[1:]
    elif sort_key.startswith("-"):
        key = sort_key[1:]

    valid_keys = {spec.key for spec in specs}
    if key not in valid_keys:
        valid = ", ".join(sorted(valid_keys))
        raise ValueError(f"Invalid sort key '{key}'. Valid: {valid}")

    def safe_value(row):
        v = row.get(key)
        if v is None:
            return float("inf") if direction == 1 else float("-inf")
        return v

    return sorted(rows, key=safe_value, reverse=(direction == -1))


def parse_filter(expr: str):
    """
    Parse expressions like:
        key=value
        key>value
        key<value
    """
    for op in ["=", ">", "<"]:
        if op in expr:
            key, val = expr.split(op, 1)
            return key.strip(), op, val.strip()

    raise ValueError(f"Invalid filter '{expr}'")


def coerce_value(val: str):
    """
    Try numeric first, fallback to string.
    """
    try:
        return float(val)
    except ValueError:
        return val.lower()


def apply_filters(rows: list[dict], specs: list, filters: tuple[str]):
    if not filters:
        return rows

    valid_keys = {spec.key for spec in specs}

    parsed = []
    for f in filters:
        key, op, val = parse_filter(f)

        if key not in valid_keys:
            valid = ", ".join(sorted(valid_keys))
            raise ValueError(f"Invalid filter key '{key}'. Valid: {valid}")

        parsed.append((key, op, coerce_value(val)))

    def match(row):
        for key, op, val in parsed:
            rv = row.get(key)

            if rv is None:
                return False

            # normalize strings
            if isinstance(rv, str):
                rv_cmp = rv.lower()
            else:
                rv_cmp = rv

            if op == "=":
                if rv_cmp != val:
                    return False
            elif op == ">":
                if not isinstance(rv_cmp, (int | float)) or rv_cmp <= val:
                    return False
            elif op == "<":
                if not isinstance(rv_cmp, (int | float)) or rv_cmp >= val:
                    return False

        return True

    return [r for r in rows if match(r)]


def apply_top(rows: list[dict], top_n: int | None):
    if top_n is None:
        return rows

    if top_n <= 0:
        return []

    return rows[:top_n]
