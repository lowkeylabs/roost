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
from owlroost.display.discovery import find_runs
from owlroost.display.loaders import load_cases
from owlroost.display.materialize import materialize_view
from owlroost.display.utils import inject_id_column
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


def discover_latest_experiment(
    results_root: Path,
    case_name: str,
):
    """
    Return newest experiment directory
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

        exp_dir = discover_latest_experiment(
            Path("results"),
            case_path.stem,
        )

        if exp_dir is None:
            raise click.ClickException("Unable to locate " "generated experiment.")

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
    default="basic",
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
    "--progress",
    default="rich",
    show_default=True,
    help=("Progress renderer: " "rich, dot, dot2, none"),
)
@click.option(
    "--run",
    is_flag=True,
    help="Generate experiments only; do not execute runs.",
)
def cmd_build(
    ctx,
    args,
    view,
    markdown,
    latex,
    progress,
    run,
):
    """
    Display available cases and build experiments.

    Examples:
      roost build
      roost build 0
      roost build case.toml
      roost build 0 solver_options.maxSpending=145
    """

    # was this function invoked as "cases" or "build"

    _invoked_as = ctx.info_name

    selectors, overrides = split_build_args(args)

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

    # ----------------------------------------
    # Discover + load case dataset
    # ----------------------------------------
    ds = load_cases(".")
    ds = prepare_dataset(
        ds,
        selectors=selectors,
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

    # ----------------------------------------
    # List available cases
    # ----------------------------------------
    if not selectors:
        table = materialize_view(
            dataset=ds,
            registry=display_registry,
            level="case",
            view_name=view,
            mode="table",
        )

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
        click.echo(f"Generated {len(generated_runs)} experiments.")

        click.echo("Experiment generation complete.")

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
