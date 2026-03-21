from __future__ import annotations

import sys
from pathlib import Path

import click
from loguru import logger
from rich.console import Console

from owlroost.domain.metrics import load_metrics
from owlroost.domain.metrics.view_registry import METRIC_VIEW_REGISTRY, get_view
from owlroost.domain.services.discovery import discover_experiments
from owlroost.domain.services.rows import build_run_rows, build_trial_rows
from owlroost.domain.views.inspect import render_table

# Ensure metrics + views are registered
load_metrics()

RESULTS_DIR = Path("results")


# =========================================================
# Helpers
# =========================================================


def view_keys(view):
    return {rm.key for rm in view}


def apply_sort(rows, view, sort_key):
    if not sort_key:
        return rows

    direction = -1
    key = sort_key

    if sort_key.startswith("+"):
        direction = 1
        key = sort_key[1:]
    elif sort_key.startswith("-"):
        key = sort_key[1:]

    valid_keys = view_keys(view)

    if key not in valid_keys:
        raise ValueError(f"Invalid sort key '{key}'. Valid: {', '.join(sorted(valid_keys))}")

    def safe_value(row):
        v = row.get(key)
        if v is None:
            return float("inf") if direction == 1 else float("-inf")
        return v

    return sorted(rows, key=safe_value, reverse=(direction == -1))


def parse_filter(expr):
    for op in ["=", ">", "<"]:
        if op in expr:
            key, val = expr.split(op, 1)
            return key.strip(), op, val.strip()
    raise ValueError(f"Invalid filter '{expr}'")


def coerce_value(val):
    try:
        return float(val)
    except ValueError:
        return val.lower()


def apply_filters(rows, view, filters):
    if not filters:
        return rows

    valid_keys = view_keys(view)

    parsed = []
    for f in filters:
        key, op, val = parse_filter(f)

        if key not in valid_keys:
            raise ValueError(f"Invalid filter key '{key}'. Valid: {', '.join(sorted(valid_keys))}")

        parsed.append((key, op, coerce_value(val)))

    def match(row):
        for key, op, val in parsed:
            rv = row.get(key)

            if rv is None:
                return False

            rv_cmp = rv.lower() if isinstance(rv, str) else rv

            if op == "=" and rv_cmp != val:
                return False
            if op == ">" and (not isinstance(rv_cmp, (int | float)) or rv_cmp <= val):
                return False
            if op == "<" and (not isinstance(rv_cmp, (int | float)) or rv_cmp >= val):
                return False

        return True

    return [r for r in rows if match(r)]


def apply_top(rows, top_n):
    if top_n is None:
        return rows
    return rows[:top_n] if top_n > 0 else []


# =========================================================
# Argument parsing
# =========================================================


def parse_args(args):
    tokens = list(args)

    def is_int(x):
        return isinstance(x, str) and x.lstrip("-").isdigit()

    level = "run"
    run_id = None
    trial_id = None

    if not tokens:
        return level, run_id, trial_id

    if len(tokens) == 1 and is_int(tokens[0]):
        return "run", int(tokens[0]), None

    if len(tokens) == 2 and is_int(tokens[0]) and is_int(tokens[1]):
        return "trial", int(tokens[0]), int(tokens[1])

    if tokens[0] == "run":
        if len(tokens) > 1 and is_int(tokens[1]):
            run_id = int(tokens[1])
        if len(tokens) > 2 and is_int(tokens[2]):
            return "trial", run_id, int(tokens[2])
        return "run", run_id, None

    if tokens[0] == "trial":
        if len(tokens) > 1 and is_int(tokens[1]):
            return "trial", None, int(tokens[1])
        return "trial", None, None

    if is_int(tokens[0]):
        run_id = int(tokens[0])
        if len(tokens) > 2 and tokens[1] == "trial" and is_int(tokens[2]):
            return "trial", run_id, int(tokens[2])
        return "run", run_id, None

    raise ValueError(f"Invalid arguments: {' '.join(tokens)}")


# =========================================================
# View helpers
# =========================================================


def list_views_for_level(level: str) -> list[str]:
    return sorted(METRIC_VIEW_REGISTRY.get(level, {}).keys())


def resolve_default_view(display_level: str, display_mode: str, row: dict | None) -> str:
    if display_level == "run":
        return "default"

    if display_level == "trial":
        if display_mode == "list":
            return "default"

        if display_mode == "detail":
            status = (row or {}).get("status")
            if status == "failed":
                return "failures"
            return "fragility"

    return "default"


def list_views_for_context(display_level: str, display_mode: str, row: dict | None):
    all_views = list_views_for_level(display_level)

    if display_level != "trial" or display_mode != "detail":
        return {"all": all_views}

    status = (row or {}).get("status")

    if status == "failed":
        return {
            "recommended": ["failures"],
            "all": all_views,
        }

    return {
        "recommended": ["fragility", "outcomes"],
        "all": all_views,
    }


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
@click.option("--views", "list_views", is_flag=True, help="List available views")
@click.option(
    "--pivot", is_flag=True, default=None, help="Render metrics as rows and items as columns"
)
def cmd_inspect(args, run_override, view_name, sort_key, top_n, filters, list_views, pivot):
    console = Console()

    # ---------------------------------------------------------
    # Parse inputs
    # ---------------------------------------------------------
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

    run_rows = build_run_rows(experiments)

    header = []
    display_level = None
    display_mode = "list"
    detail_row = None

    # =========================================================
    # RUN LIST
    # =========================================================
    if level == "run" and run_id is None:
        display_level = "run"
        working_rows = run_rows

        header = ["[bold]Runs (all experiments)[/bold]"]

    else:
        if run_id is None:
            run_id = len(run_rows) - 1

        if run_id < 0 or run_id >= len(run_rows):
            console.print("[red]Invalid run id[/red]")
            return

        selected = run_rows[run_id]
        ref = selected["_ref"]

        exp = experiments[ref["exp_index"]]
        run = exp.runs[ref["run_index"]]

        trial_rows = build_trial_rows(exp, run)

        # TRIAL LIST
        if trial_id is None:
            display_level = "trial"
            display_mode = "list"
            working_rows = trial_rows

            header = [
                "[bold cyan]TRIAL[/bold cyan]",
                f"[dim]Exp {ref['exp_index']} | Run {ref['run_index']}[/dim]",
                f"[dim]{run.path}[/dim]",
            ]

        # SINGLE TRIAL
        else:
            if trial_id < 0 or trial_id >= len(trial_rows):
                console.print("[red]Invalid trial id[/red]")
                return

            display_level = "trial"
            display_mode = "detail"
            detail_row = trial_rows[trial_id]
            working_rows = [detail_row]

            trial = run.trials[trial_id]

            header = [
                f"[bold]Run {ref['run_index']} - Trial {trial_id}[/bold]",
                f"[dim]{trial.path}[/dim]",
            ]

    # ---------------------------------------------------------
    # View listing
    # ---------------------------------------------------------
    if list_views:
        context_views = list_views_for_context(display_level, display_mode, detail_row)

        console.print()
        console.print(f"[bold]Available views for level '{display_level}':[/bold]")
        console.print("[dim](use --view <name>)[/dim]")

        if "recommended" in context_views:
            console.print("\n[bold]Recommended:[/bold]")
            for v in context_views["recommended"]:
                console.print(f"  {v}")

        console.print("\n[bold]All:[/bold]")
        for v in context_views["all"]:
            console.print(f"  {v}")

        console.print()
        return

    # ---------------------------------------------------------
    # Default view override (only if user didn't specify)
    # ---------------------------------------------------------
    user_provided_view = "--view" in sys.argv

    if not user_provided_view:
        view_name = resolve_default_view(display_level, display_mode, detail_row)

    # ---------------------------------------------------------
    # Resolve view
    # ---------------------------------------------------------
    try:
        selected_view, layout = get_view(display_level, view_name)
    except KeyError:
        available = ", ".join(sorted(METRIC_VIEW_REGISTRY[display_level].keys()))
        console.print(f"[red]Unknown view '{view_name}'[/red]")
        console.print(f"[dim]Available: {available}[/dim]")
        return

    logger.debug(f"pivot: {pivot}")
    if pivot:
        layout = "pivot"

    # ---------------------------------------------------------
    # Apply filters/sort/top
    # ---------------------------------------------------------
    working_rows = apply_filters(working_rows, selected_view, filters)
    working_rows = apply_sort(working_rows, selected_view, sort_key)
    working_rows = apply_top(working_rows, top_n)

    final_rows = working_rows

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------
    if pivot:
        header.append(f"[dim]View: {display_level}:{view_name} PIVOT[/dim]")
    else:
        header.append(f"[dim]View: {display_level}:{view_name}[/dim]")

    # ---------------------------------------------------------
    # Render
    # ---------------------------------------------------------
    console.print()
    for line in header:
        console.print(line)
    console.print()

    render_table(console, final_rows, selected_view, layout=layout)
