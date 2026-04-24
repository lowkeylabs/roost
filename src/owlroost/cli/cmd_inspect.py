# src/owlroost/cli/cmd_inspect.py

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

import click
import yaml
from rich.console import Console

from owlroost.domain.metrics import load_metrics
from owlroost.domain.metrics.metric_spec import EXPLAIN_FACETS, facet_help
from owlroost.domain.metrics.view_registry import (
    get_view,
    list_views,
    resolve_default_view,
    view_help,
)
from owlroost.domain.services.discovery import discover_experiments
from owlroost.domain.services.query import apply_filters, apply_sort, apply_top
from owlroost.domain.services.render_table import render_table
from owlroost.domain.services.results_pruning import prune_empty_experiments
from owlroost.domain.services.rows import build_run_rows, build_trial_rows

# Ensure metrics + views are registered
load_metrics()

RESULTS_DIR = Path("results")
REPORTS_DIR = Path("reports")
TEMPLATE_DIR = Path("/home/john/projects/owl-roost/templates")


EXPLAIN_SPECIAL = {"none", "help"}
EXPLAIN_ALL = EXPLAIN_FACETS | EXPLAIN_SPECIAL

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
# Explain parser
# =========================================================


def parse_explain(explain_opts, view_explain):
    """
    Normalize CLI explain options into a set of facets.

    Returns:
        set[str]
    """

    # ----------------------------------------
    # No CLI input → fall back to view default
    # ----------------------------------------
    if not explain_opts:
        return {"all"} if view_explain else set()

    parts = set()

    for opt in explain_opts:
        for p in opt.split(","):
            p = p.strip()
            if not p:
                continue
            if p not in EXPLAIN_ALL:
                valid = ", ".join(sorted(EXPLAIN_ALL))
                raise ValueError(f"Invalid explain option '{p}'. Valid: {valid}")
            parts.add(p)

    # ----------------------------------------
    # Special handling
    # ----------------------------------------
    if "none" in parts:
        return set()

    return set(parts)


def runrow_to_dict(r):
    # Case 1: already a dict → return as-is
    if isinstance(r, dict):
        return r

    # Case 2: dataclass → convert
    d = vars(r).copy()

    # Preserve _ref if present
    if hasattr(r, "_ref"):
        d["_ref"] = r._ref

    return d


def parse_delete_ids(delete_str: str) -> list[int]:
    ids = set()

    for part in delete_str.split(","):
        part = part.strip()
        if not part:
            continue

        # ----------------------------------------
        # Range: "start-end"
        # ----------------------------------------
        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                start = int(start_str)
                end = int(end_str)
            except ValueError:
                raise click.ClickException(f"Invalid range: '{part}'") from None

            if start > end:
                raise click.ClickException(f"Invalid range (start > end): '{part}'")

            ids.update(range(start, end + 1))
            continue

        # ----------------------------------------
        # Single ID
        # ----------------------------------------
        if not part.isdigit():
            raise click.ClickException(f"Invalid delete id: '{part}'")

        ids.add(int(part))

    return sorted(ids)


# =========================================================
# CLI
# =========================================================


@click.command(name="inspect")
@click.argument("args", nargs=-1)
@click.option("--case", "case_override", type=int)
@click.option("--experiment", "--exp", "exp_override", type=int)
@click.option("--run", "run_override", type=int)
@click.option("--view", "view_name", default=None)
@click.option("--sort", "sort_key", type=str)
@click.option("--top", "top_n", type=int)
@click.option("--filter", "filters", multiple=True)
@click.option("--views", "list_views_flag", is_flag=True, help="List available views")
@click.option(
    "--pivot", is_flag=True, default=None, help="Render metrics as rows and items as columns"
)
@click.option(
    "--explain",
    "explain_opts",
    multiple=True,
    help=(
        "Explanation facets (repeatable or comma-separated): " f"{', '.join(sorted(EXPLAIN_ALL))}"
    ),
)
@click.option(
    "--trials",
    "trials_flag",
    is_flag=True,
    help="Show trial-level rows instead of run-level rows",
)
@click.option(
    "--delete",
    type=str,
    help="Delete one or more runs by ID (comma-separated, run/table view only).",
)
@click.option(
    "--to-report",
    type=str,
    default=None,
    metavar="NAME",
    help="Create a report workspace with the given name under reports/<case>/NAME.",
)
@click.option(
    "--purge",
    is_flag=True,
    help="Delete duplicate runs, keeping only the most recent instance.",
)
def cmd_inspect(
    args,
    case_override,
    exp_override,
    run_override,
    view_name,
    sort_key,
    top_n,
    filters,
    list_views_flag,
    pivot,
    explain_opts,
    trials_flag,
    delete,
    to_report,
    purge,
):
    console = Console()

    # ---------------------------------------------------------
    # Parse inputs
    # ---------------------------------------------------------
    try:
        level, run_id, trial_id = parse_args(args)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return

    if trials_flag:
        level = "trial"
        run_id = None
        trial_id = None

    if run_override is not None:
        run_id = run_override

    if not RESULTS_DIR.exists():
        console.print("[red]Results directory not found[/red]")
        return

    if delete is not None:
        if level != "run":
            raise click.ClickException("--delete only supported in run view")

        if level == "pivot":
            raise click.ClickException("--delete not supported in pivot view")

    experiments = discover_experiments(RESULTS_DIR)

    # ---------------------------------------------------------
    # Apply case / experiment filters (NEW)
    # ---------------------------------------------------------
    if case_override is not None:
        experiments = [e for e in experiments if getattr(e, "case_id", None) == case_override]

    if exp_override is not None:
        experiments = [e for e in experiments if getattr(e, "id", None) == exp_override]

    if not experiments:
        console.print(
            f"[red]No experiments found for case={case_override}, experiment={exp_override}[/red]"
        )
        return

    run_rows = build_run_rows(experiments)
    trial_rows = build_trial_rows(experiments)

    header = []
    display_level = None
    display_mode = "list"
    detail_row = None

    # =========================================================
    # TRIAL LIST (NEW)
    # =========================================================
    if level == "trial" and run_id is None:
        display_level = "trial"
        display_mode = "list"

        working_rows = trial_rows

        header = ["[bold]Trials (all experiments)[/bold]"]

    # =========================================================
    # RUN LIST
    # =========================================================

    elif level == "run" and run_id is None:
        display_level = "run"
        working_rows = run_rows

        # working_rows = [vars(r) for r in run_rows]
        working_rows = [runrow_to_dict(r) for r in run_rows]

        if case_override is not None and exp_override is not None:
            case_name = experiments[0].case
            header = [f"[bold]Runs (case {case_override}: {case_name}, exp {exp_override})[/bold]"]

        elif case_override is not None:
            case_name = experiments[0].case
            header = [f"[bold]Runs (case {case_override}: {case_name})[/bold]"]

        elif exp_override is not None:
            header = [f"[bold]Runs (experiment {exp_override})[/bold]"]

        else:
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

        trial_rows = build_trial_rows([exp])
        trial_rows = [r for r in trial_rows if r.get("run") == run.name]

        # TRIAL LIST
        if trial_id is None:
            display_level = "run"
            display_mode = "summary"
            working_rows = [selected]

            working_rows = [runrow_to_dict(selected)]

            header = [
                "[bold cyan]RUN[/bold cyan]",
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
    if view_name == "help" or list_views_flag:
        tag_filter = None

        # Only treat args as tag filter when NOT selecting a run/trial
        if view_name == "help" and level == "run" and run_id is None and args:
            tag_filter = args[0]

        console.print(view_help(display_level, display_mode, detail_row, tag_filter))
        return

    # ---------------------------------------------------------
    # Default view override (only if user didn't specify)
    # ---------------------------------------------------------
    if 0:
        user_provided_view = "--view" in sys.argv

        if not user_provided_view:
            view_name = resolve_default_view(display_level, display_mode, detail_row)

            # -----------------------------------------------------
            # Optional: smarter defaults for run summary (NEW)
            # -----------------------------------------------------
            if display_level == "run" and display_mode == "summary":
                trial_cnt = working_rows[0].get("trial_cnt", 1)

                if trial_cnt == 1:
                    view_name = "summary"
                else:
                    view_name = "diagnostics"
    if view_name is None:
        view_name = resolve_default_view(display_level, display_mode, detail_row)

    # ---------------------------------------------------------
    # Resolve view
    # ---------------------------------------------------------
    try:
        selected_view, layout, view_explain = get_view(display_level, view_name)
    except KeyError as e:
        available = ", ".join(list_views(display_level))
        console.print(f"[red]Failed to load view '{view_name}'[/red]")
        console.print(f"[dim]Available: {available}[/dim]")
        console.print(f"[yellow]Error: {e}[/yellow]")  # 🔥 THIS IS THE KEY LINE
        return

    # ---------------------------------------------------------
    # Layout defaults based on display_mode (NEW)
    # ---------------------------------------------------------
    if pivot is True:
        layout = "pivot"
    elif pivot is None:
        # default behavior
        if display_mode in ("summary", "detail"):
            layout = "pivot"

    if any(opt.strip() == "help" for opt in explain_opts):
        console.print(facet_help(explain_opts))
        return

    try:
        explain_set = parse_explain(explain_opts, view_explain)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return

    # ---------------------------------------------------------
    # Apply filters/sort/top
    # ---------------------------------------------------------
    working_rows = apply_filters(working_rows, selected_view, filters)
    working_rows = apply_sort(working_rows, selected_view, sort_key)
    working_rows = apply_top(working_rows, top_n)

    final_rows = working_rows

    # ---------------------------------------------------------
    # PURGE duplicate runs (keep latest only)
    # ---------------------------------------------------------

    if purge:
        if display_level != "run":
            raise click.ClickException("--purge only supported in run view")

        if layout == "pivot":
            raise click.ClickException("--purge not supported in pivot view")

        # Identify duplicate-but-not-latest runs
        targets = []

        for i, row in enumerate(final_rows):
            if row.get("is_duplicate") and not row.get("is_latest_duplicate"):
                ref = row["_ref"]
                exp = experiments[ref["exp_index"]]
                run = exp.runs[ref["run_index"]]
                targets.append((i, Path(run.path)))

        if not targets:
            console.print("[green]No duplicate runs to purge.[/green]")
            return

        # Confirm
        console.print("[bold red]Purge the following duplicate runs:[/bold red]")
        for i, path in targets:
            console.print(f"  ID {i}: {path}")

        click.confirm("Proceed?", abort=True)

        # Delete
        for i, path in targets:
            if path.exists():
                shutil.rmtree(path)
                console.print(f"[green]Deleted {i}: {path}[/green]")
            else:
                console.print(f"[yellow]Skipping {i}: path not found[/yellow]")

        # ----------------------------------------
        # NEW: prune empty experiment folders
        # ----------------------------------------
        prune_empty_experiments(RESULTS_DIR, console)

        return

    # ---------------------------------------------------------
    # Delete using the row ID of filtered rows.
    # ---------------------------------------------------------

    if delete is not None:
        if display_level != "run":
            raise click.ClickException("--delete only supported in run view")

        if layout == "pivot":
            raise click.ClickException("--delete not supported in pivot view")

        delete_ids = parse_delete_ids(delete)

        if not delete_ids:
            raise click.ClickException("No valid IDs provided to --delete")

        # Validate IDs
        max_id = len(final_rows) - 1
        for i in delete_ids:
            if i < 0 or i > max_id:
                raise click.ClickException(f"Invalid ID {i}. Must be 0–{max_id}")

        # Resolve run paths
        targets = []
        for i in delete_ids:
            row = final_rows[i]
            ref = row["_ref"]
            exp = experiments[ref["exp_index"]]
            run = exp.runs[ref["run_index"]]
            targets.append((i, Path(run.path)))

        # Confirm once
        console.print("[bold red]Delete the following runs:[/bold red]")
        for i, path in targets:
            console.print(f"  ID {i}: {path}")

        click.confirm("Proceed?", abort=True)

        for i, path in targets:
            if path.exists():
                shutil.rmtree(path)
                console.print(f"[green]Deleted {i}: {path}[/green]")
            else:
                console.print(f"[yellow]Skipping {i}: path not found[/yellow]")

        return

    # ---------------------------------------------------------
    # Capture report bundle (metadata.yaml)
    # ---------------------------------------------------------

    if to_report is not None:
        # ----------------------------------------
        # Resolve case name
        # ----------------------------------------
        case_name = experiments[0].case if experiments else "unknown"

        case_dir = REPORTS_DIR / case_name
        case_dir.mkdir(parents=True, exist_ok=True)

        # ----------------------------------------
        # Extract run paths (CRITICAL for reproducibility)
        # ----------------------------------------
        run_paths = []
        run_refs = []
        run_objs = []  # ✅ NEW: keep run objects

        for row in final_rows:
            ref = row["_ref"]
            exp = experiments[ref["exp_index"]]
            run = exp.runs[ref["run_index"]]

            run_paths.append(str(Path(run.path)))
            run_refs.append(ref)
            run_objs.append(run)  # ✅ NEW

        # ----------------------------------------
        # Resolve report folder name
        # ----------------------------------------
        report_name = (to_report or "").strip()

        if not report_name:
            # Auto-generate report_N
            existing = {p.name for p in case_dir.iterdir() if p.is_dir()}

            i = 0
            while True:
                candidate = f"report_{i}"
                if candidate not in existing:
                    report_name = candidate
                    break
                i += 1
        else:
            # Explicit name must not exist
            if (case_dir / report_name).exists():
                raise click.ClickException(
                    f"Report folder already exists: {case_dir / report_name}"
                )

        bundle_dir = case_dir / report_name
        bundle_dir.mkdir(parents=True, exist_ok=False)

        # ----------------------------------------
        # Build metadata
        # ----------------------------------------
        metadata = {
            "version": 1,
            # ----------------------------------------
            # Bundle identity
            # ----------------------------------------
            "bundle": {
                "name": report_name,
                "created_at": datetime.now().isoformat(),
                "command": " ".join(sys.argv),
            },
            # ----------------------------------------
            # Paths (critical for portability + reproducibility)
            # ----------------------------------------
            "paths": {
                # Absolute paths (primary reference)
                "project_root": str(Path.cwd().resolve()),
                "results_dir": str(RESULTS_DIR.resolve()),
                "reports_dir": str(REPORTS_DIR.resolve()),
                # Optional future use
                # "data_dir": str((bundle_dir / "data").resolve()),
            },
            # ----------------------------------------
            # Runs (portable + reproducible)
            # ----------------------------------------
            "runs": [
                {
                    # Preferred: relative to results_dir
                    "path": str(Path(p).resolve().relative_to(RESULTS_DIR.resolve())),
                    # Fallback: absolute (in case relocation fails)
                    "abs_path": str(Path(p).resolve()),
                    # ✅ NEW: stable logical identity
                    "signature": getattr(run, "signature", None),
                    # ✅ OPTIONAL: may go stale, safe to include
                    "ref": {
                        "exp_index": ref["exp_index"],
                        "run_index": ref["run_index"],
                    },
                }
                for p, run, ref in zip(run_paths, run_objs, run_refs, strict=False)
            ],
            # ----------------------------------------
            # Future extensions (safe placeholders)
            # ----------------------------------------
            "options": {
                # e.g., include_data=True in future
                # "include_data": False,
            },
            "notes": "",
        }

        # ----------------------------------------
        # Write metadata.yaml
        # ----------------------------------------
        metadata_path = bundle_dir / "metadata.yaml"

        with open(metadata_path, "w") as f:
            yaml.dump(metadata, f, sort_keys=False)

        # ----------------------------------------
        # Copy templates into bundle (optional)
        # ----------------------------------------
        template_list = ["simple"]
        if template_list:
            template_dest = bundle_dir

            for name in template_list:
                src = TEMPLATE_DIR / f"{name}.qmd"
                dst = template_dest / f"{name}.qmd"

                if src.exists():
                    shutil.copy(src, dst)
                else:
                    console.print(f"[yellow]Template not found: {name}[/yellow]")

            src = TEMPLATE_DIR / "_quarto.yml"
            dst = template_dest / "_quarto.yml"
            if src.exists():
                shutil.copy(src, dst)
            else:
                console.print("[yellow]Project file not found: _quarto.yml[/yellow]")

        # ----------------------------------------
        # Done
        # ----------------------------------------
        console.print()
        console.print(f"[green]Report workspace created:[/green] {bundle_dir}")
        console.print(f"[dim]{metadata_path}[/dim]")

        return

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------
    mode_tag = f" ({display_mode})" if display_mode != "list" else ""

    if pivot:
        header.append(f"[dim]View: {display_level}:{view_name}{mode_tag} PIVOT[/dim]")
    else:
        header.append(f"[dim]View: {display_level}:{view_name}{mode_tag}[/dim]")

    # ---------------------------------------------------------
    # Render
    # ---------------------------------------------------------
    console.print()
    for line in header:
        console.print(line)
    console.print()

    render_table(console, final_rows, selected_view, layout=layout, explain=explain_set)
