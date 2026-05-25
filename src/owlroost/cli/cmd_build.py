# src/owlroost/cli/cmd_build.py

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click

from owlroost.cli.utils import (
    prepare_dataset,
    render_table,
    resolve_renderer,
    split_build_args,
)
from owlroost.core.run_owl_executor import execute_runs
from owlroost.display.bootstrap import build_display_registry
from owlroost.display.compare import materialize_compare_table
from owlroost.display.discovery import find_runs
from owlroost.display.loaders import load_cases
from owlroost.display.utils import attach_row_ids, inject_id_column, render_field_help
from owlroost.metrics.registry.bootstrap import build_metrics_registry
from owlroost.schema.bootstrap import build_registry


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def resolve_case_selection(
    arg: str,
    dataset,
):
    """
    Resolve CLI selection into dataset row.

    Selection may be:
    - numeric row ID
    - TOML file path
    """

    rows = dataset.rows

    # ----------------------------------------
    # Prefer explicit file path if it exists
    # ----------------------------------------
    path = Path(arg)

    if path.exists():
        resolved = path.resolve()

        for r in rows:
            if Path(r["_path"]).resolve() == resolved:
                return r

        raise click.ClickException("File not recognized " f"as case: {arg}")

    # ----------------------------------------
    # Numeric ID
    # ----------------------------------------
    if arg.isdigit():
        idx = int(arg)

        if idx < 0 or idx >= len(rows):
            raise click.ClickException(f"Invalid ID: {idx}")

        return rows[idx]

    # ----------------------------------------
    # Unknown selection
    # ----------------------------------------
    raise click.ClickException("Invalid case selection: " f"{arg}")


def build_hydra_command(
    case_path: Path,
    overrides: list[str],
):
    """
    Construct Hydra multirun command.
    """

    package_root = Path(__file__).parents[1]

    conf_dir = package_root / "conf"

    cmd = [
        sys.executable,
        "-m",
        "owlroost.hydra.generate_trials",
        "--multirun",
        ("--config-path=" f"{str(conf_dir.resolve())}"),
        "--config-name=config",
        ("case.file=" f"{str(case_path.resolve())}"),
        ("case.name=" f"{case_path.stem}"),
    ]

    cmd.extend(overrides)

    return cmd


def discover_latest_session(
    results_root: Path,
    case_name: str,
):
    """
    Return newest session directory
    for case.
    """

    case_root = results_root / case_name

    if not case_root.exists():
        return None

    candidates = []

    for date_dir in case_root.iterdir():
        if not date_dir.is_dir():
            continue

        for exp_dir in date_dir.iterdir():
            if not exp_dir.is_dir():
                continue

            if (exp_dir / "multirun.yaml").exists():
                candidates.append(exp_dir)

    if not candidates:
        return None

    return sorted(candidates)[-1]


# ---------------------------------------------------------
# Hydra execution
# ---------------------------------------------------------
def run_hydra_build(
    case_path: Path,
    overrides: list[str],
):
    """
    Execute Hydra generator in multirun mode.

    Returns:
        list[Path] of generated run directories
    """
    cmd = build_hydra_command(
        case_path,
        overrides,
    )

    #    click.echo("Running Hydra:")
    #    logger.debug(f"Hydra CLI: {(" ".join(cmd))}")
    #    click.echo()

    try:
        subprocess.run(
            cmd,
            check=True,
        )

        exp_dir = discover_latest_session(
            Path("results"),
            case_path.stem,
        )

        if exp_dir is None:
            raise click.ClickException("Unable to locate " "generated session.")

        runs = find_runs(exp_dir)
        if not runs:
            raise click.ClickException(f"No runs discovered in {exp_dir}")
        return runs

    except subprocess.CalledProcessError as exc:
        raise click.ClickException("Hydra run failed " f"({exc.returncode})") from exc


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------
@click.command("build")
@click.pass_context
@click.argument(
    "args",
    nargs=-1,
)
@click.option(
    "--view",
    default=None,
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
    help="Render transposed pivot layout.",
)
@click.option(
    "--compare",
    is_flag=True,
    help="Structural side-by-side comparison.",
)
@click.option(
    "--diff",
    is_flag=True,
    help="Show only differing structural fields.",
)
@click.option(
    "--explain",
    type=str,
    help=(
        "Explanation facets. " "Comma-separated list from: " "variables,values,sources,debug,all"
    ),
)
@click.option(
    "--filter",
    "filters",
    multiple=True,
    help=(
        "Filter rows. "
        "Examples: "
        "display.total_savings>1000000 "
        "optimization_parameters.objective=maxBequest"
    ),
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
    help=("Progress renderer: " "rich, dot, dot2, none"),
)
@click.option(
    "--run",
    is_flag=True,
    help="Generate sessions only; do not execute runs.",
)
def cmd_build(
    ctx,
    args,
    view,
    markdown,
    latex,
    pivot,
    compare,
    diff,
    explain,
    filters,
    sort,
    top,
    progress,
    run,
):
    """
    Display available cases and build sessions.

    Examples:
      roost build
      roost build 0
      roost build case.toml
      roost build 0 solver_options.maxSpending=145
    """

    # was this function invoked as "cases" or "build"

    _invoked_as = ctx.info_name
    # set default view to "build" or "cases"
    # will automatically load as "case" view
    if view is None:
        view = ctx.info_name

    selectors, overrides = split_build_args(args)
    is_cases_command = _invoked_as == "cases"

    #    if overrides_request_trials(overrides):
    #        if run:
    #            click.echo("INFO: trials_per_run > 0 detected; " "enabling --build-only automatically.")
    #
    #        build_only = True

    schema_registry = build_registry()
    metrics_registry = build_metrics_registry()
    display_registry = build_display_registry(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
    )

    # =====================================================
    # Context-sensitive CLI help
    # =====================================================

    ds = load_cases(".")
    ds = attach_row_ids(ds)

    if "help" in (filters or ()):
        render_field_help(
            dataset=ds,
            registry=display_registry,
            level="case",
            view_name=view,
            mode="view",
            title="Available filter fields",
            examples=[
                "--filter id=in:1,2,3",
                "--filter display.total_savings>2000000",
                "--filter optimization_parameters.objective=maxBequest",
                "--filter rates_selection.method=user",
            ],
        )

        return

    if "help-all" in (filters or ()):
        render_field_help(
            dataset=ds,
            registry=display_registry,
            level="case",
            view_name=view,
            mode="all",
            title="All queryable fields",
        )

        return

    if sort == "help":
        render_field_help(
            dataset=ds,
            registry=display_registry,
            level="case",
            view_name=view,
            mode="view",
            title="Available filter fields",
            examples=[
                "--sort display.total_savings",
                "--sort -display.total_savings",
                "--sort display.fixed_income",
            ],
        )

        return

    if sort == "help-all":
        render_field_help(
            dataset=ds,
            registry=display_registry,
            level="case",
            view_name=view,
            mode="all",
            title="Available filter fields",
            examples=[
                "--sort display.total_savings",
                "--sort -display.total_savings",
                "--sort display.fixed_income",
            ],
        )

        return

    if str(top).lower() == "help":
        click.echo()
        click.echo("Limit displayed rows.")
        click.echo()
        click.echo("Examples:")
        click.echo()
        click.echo("  --top 5")
        click.echo("  --top 10")
        click.echo()

        return

    # ----------------------------------------
    # Discover + load case dataset
    # ----------------------------------------
    ds = prepare_dataset(
        ds,
        selectors=selectors,
        filters=filters,
        sort=sort,
        top=top,
    )

    if not ds.rows:
        click.echo("No case TOML files found.")
        return

    # ----------------------------------------
    # Resolve renderer
    # ----------------------------------------
    renderer = resolve_renderer(
        markdown,
        latex,
    )

    # =====================================================
    # Normalize explain facets
    # =====================================================

    explain_facets = set()

    if explain:
        explain_facets = {x.strip() for x in explain.split(",") if x.strip()}

        if "all" in explain_facets:
            explain_facets = {
                "variables",
                "values",
                "sources",
                "debug",
            }

    # =====================================================
    # Structural compare/diff mode
    #
    # Also automatically enabled when:
    #   roost cases <single-id>
    #
    # because user intent is usually:
    #   "show me full case contents"
    # =====================================================

    auto_compare = (
        is_cases_command
        and len(ds.rows) == 1
        and not compare
        and not diff
        and not pivot
        and view == "basic"
    )

    if compare or diff or auto_compare:
        table = materialize_compare_table(
            dataset=ds,
            diff_only=diff,
            explain=explain_facets,
        )

        output = render_table(
            table,
            renderer,
        )

        if output:
            click.echo(output)

        return

    # ----------------------------------------
    # List available cases
    # ----------------------------------------
    if is_cases_command or (not selectors and not overrides):
        table = ds.view(
            registry=display_registry,
            name=view,
            layout="pivot" if pivot else "table",
            explain=explain_facets,
        )

        if not pivot:
            table = inject_id_column(
                table,
                ds,
            )

        output = render_table(
            table,
            renderer,
        )

        if output:
            click.echo(output)

        return

    # ----------------------------------------
    # Resolve selected case
    # ----------------------------------------
    selected_rows = ds.rows

    if not selected_rows:
        raise click.ClickException("No matching case selections.")

    labels = []

    for row in selected_rows:
        case_path = Path(row["_path"]).resolve()

        labels.append(f"{case_path.stem}/run_0")

    max_label_width = max(len(x) for x in labels)

    os.environ["OWLROOST_PROGRESS_LABEL_WIDTH"] = str(max_label_width)

    generated_runs = []

    for row in selected_rows:
        case_path = Path(row["_path"]).resolve()

        # ----------------------------------------
        # Launch Hydra build
        # ----------------------------------------
        runs = run_hydra_build(
            case_path,
            list(overrides),
        )

        generated_runs.extend(runs)

    # ----------------------------------------
    # Build-only exit
    # ----------------------------------------

    if not run:
        click.echo(f"Generated {len(generated_runs)} sessions.")

        click.echo("session generation complete.")

        return

    # ----------------------------------------
    # Execute all runs
    # ----------------------------------------

    if not generated_runs:
        click.echo("No runs available for execution.")

        return

    execute_runs(
        generated_runs,
        progress=progress,
    )
