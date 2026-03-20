from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from owlroost.domain.metrics import load_metrics
from owlroost.domain.metrics.view_registry import get_view
from owlroost.domain.services.aggregation import aggregate_rows
from owlroost.domain.services.context import enrich_row
from owlroost.domain.services.discovery import discover_experiments
from owlroost.domain.services.metrics import build_trial_row
from owlroost.domain.views.inspect import render_run, render_trial

# Ensure metrics + views are registered
load_metrics()

RESULTS_DIR = Path("results")


# =========================================================
# Helpers
# =========================================================


def base_metric_specs(resolved_view):
    seen = {}
    for rm in resolved_view:
        seen[rm.spec.key] = rm.spec
    return list(seen.values())


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

    valid_keys = {rm.key for rm in specs}
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
    for op in ["=", ">", "<"]:
        if op in expr:
            key, val = expr.split(op, 1)
            return key.strip(), op, val.strip()
    raise ValueError(f"Invalid filter '{expr}'")


def coerce_value(val: str):
    try:
        return float(val)
    except ValueError:
        return val.lower()


def apply_filters(rows: list[dict], specs: list, filters: tuple[str]):
    if not filters:
        return rows

    valid_keys = {rm.key for rm in specs}

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

            rv_cmp = rv.lower() if isinstance(rv, str) else rv

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


# =========================================================
# Argument parsing (NEW CORE)
# =========================================================


def parse_args(args):
    """
    Returns: (level, run_id, trial_id)
    """

    tokens = list(args)

    def is_int(x):
        return isinstance(x, str) and x.lstrip("-").isdigit()

    level = "run"
    run_id = None
    trial_id = None

    if not tokens:
        return level, run_id, trial_id

    # inspect 3
    if len(tokens) == 1 and is_int(tokens[0]):
        return "run", int(tokens[0]), None

    # inspect 3 4
    if len(tokens) == 2 and is_int(tokens[0]) and is_int(tokens[1]):
        return "trial", int(tokens[0]), int(tokens[1])

    # inspect run 3 [4]
    if tokens[0] == "run":
        if len(tokens) > 1 and is_int(tokens[1]):
            run_id = int(tokens[1])
        if len(tokens) > 2 and is_int(tokens[2]):
            return "trial", run_id, int(tokens[2])
        return "run", run_id, None

    # inspect trial 4
    if tokens[0] == "trial":
        if len(tokens) > 1 and is_int(tokens[1]):
            return "trial", None, int(tokens[1])
        return "trial", None, None

    # inspect 3 trial 4
    if is_int(tokens[0]):
        run_id = int(tokens[0])
        if len(tokens) > 2 and tokens[1] == "trial" and is_int(tokens[2]):
            return "trial", run_id, int(tokens[2])
        return "run", run_id, None

    raise ValueError(f"Invalid arguments: {' '.join(tokens)}")


# =========================================================
# CLI
# =========================================================


@click.command(name="inspect")
@click.argument("args", nargs=-1)
@click.option("--run", "run_override", type=int)
@click.option("--view", "view_name", default="default")
@click.option("--sort", "sort_key", type=str)
@click.option("--top", "top_n", type=int)
@click.option("--filter", "filters", multiple=True)
def cmd_inspect(
    args,
    run_override: int | None,
    view_name: str,
    sort_key: str | None,
    top_n: int | None,
    filters: list[str],
):
    console = Console()

    try:
        level, run_id, trial_id = parse_args(args)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return

    if run_override is not None:
        run_id = run_override

    if not RESULTS_DIR.exists():
        console.print("[red]Results directory not found[/red]")
        return

    experiments = discover_experiments(RESULTS_DIR)

    if not experiments:
        console.print("[yellow]No experiments found[/yellow]")
        return

    trial_view = get_view("trial", view_name)
    run_view = get_view("run", view_name)

    # =========================================================
    # BUILD GLOBAL RUN LIST
    # =========================================================

    run_rows = []

    for exp_index, exp in enumerate(experiments):
        for run_index, r in enumerate(exp.runs):
            trial_rows = []

            for trial in r.trials:
                base = enrich_row({}, exp, r, trial)

                row = build_trial_row(
                    trial.path,
                    base_metric_specs(run_view),
                    base_row=base,
                )
                if row:
                    trial_rows.append(row)

            if not trial_rows:
                continue

            summary = aggregate_rows(trial_rows, run_view)

            summary["_ref"] = {
                "exp_index": exp_index,
                "run_index": run_index,
            }

            run_rows.append(summary)

    if not run_rows:
        console.print("[yellow]No metrics found[/yellow]")
        return

    try:
        run_rows = apply_filters(run_rows, run_view, filters)
        run_rows = apply_sort(run_rows, run_view, sort_key)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return

    run_rows = apply_top(run_rows, top_n)

    # =========================================================
    # RUN LIST
    # =========================================================

    if run_id is None and level == "run":
        console.print("\n[bold]Runs (all experiments)[/bold]")
        console.print(f"[dim]view: run:{view_name}[/dim]\n")
        render_run(console, run_rows, run_view)
        return

    # =========================================================
    # SELECT RUN
    # =========================================================

    if run_id is None:
        run_id = len(run_rows) - 1

    if run_id < 0 or run_id >= len(run_rows):
        console.print("[red]Invalid run id[/red]")
        return

    selected = run_rows[run_id]
    ref = selected["_ref"]

    exp = experiments[ref["exp_index"]]
    run = exp.runs[ref["run_index"]]

    # =========================================================
    # BUILD TRIAL ROWS
    # =========================================================

    rows = []

    for trial in run.trials:
        base = enrich_row({}, exp, run, trial)

        row = build_trial_row(
            trial.path,
            base_metric_specs(trial_view),
            base_row=base,
        )
        if row:
            rows.append(row)

    if not rows:
        console.print("[yellow]No metrics found[/yellow]")
        return

    try:
        rows = apply_filters(rows, trial_view, filters)
        rows = apply_sort(rows, trial_view, sort_key)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return

    rows = apply_top(rows, top_n)

    # =========================================================
    # TRIAL LIST
    # =========================================================

    if trial_id is None:
        console.print(f"\n[bold cyan]TRIAL[/bold cyan] [dim]|[/dim] [bold]{view_name}[/bold]\n")
        console.print(f"[dim]Exp {ref['exp_index']} | Run {ref['run_index']}[/dim]")
        console.print(f"[dim]{run.path}[/dim]\n")

        render_run(console, rows, trial_view)
        return

    # =========================================================
    # SINGLE TRIAL
    # =========================================================

    if trial_id < 0 or trial_id >= len(run.trials):
        console.print("[red]Invalid trial id[/red]")
        return

    trial = run.trials[trial_id]

    base = enrich_row({}, exp, run, trial)

    row = build_trial_row(
        trial.path,
        base_metric_specs(trial_view),
        base_row=base,
    )

    if not row:
        console.print("[red]No _metrics.json found[/red]")
        return

    console.print(f"\n[bold]Trial {trial_id} (Run {ref['run_index']})[/bold]")
    console.print(f"[dim]{trial.path}[/dim]\n")

    render_trial(console, row, trial_view)
