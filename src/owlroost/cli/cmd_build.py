# src/owlroost/cli/cmd_build.py

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

from owlroost.core.run_owl_executor import (
    execute_runs,
)
from owlroost.display.bootstrap import (
    build_display_registry,
)
from owlroost.display.discovery import (
    find_runs,
)
from owlroost.display.loaders import (
    load_cases,
)
from owlroost.display.materialize import (
    materialize_view,
)
from owlroost.display.renderers.latex_table import (
    render_latex_table,
)
from owlroost.display.renderers.markdown_table import (
    render_markdown_table,
)
from owlroost.display.renderers.rich_table import (
    render_rich_table,
)
from owlroost.display.utils import (
    attach_row_ids,
    inject_id_column,
)
from owlroost.metrics.registry.bootstrap import (
    build_metrics_registry,
)
from owlroost.schema.bootstrap import (
    build_registry,
)


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


def render_table(
    table,
    renderer,
):
    """
    Dispatch table renderer.
    """

    if renderer == "markdown":
        return render_markdown_table(table)

    if renderer == "latex":
        return render_latex_table(table)

    return render_rich_table(table)


def resolve_renderer(
    markdown=False,
    latex=False,
):
    """
    Resolve renderer name from CLI flags.
    """

    if markdown:
        return "markdown"

    if latex:
        return "latex"

    return "rich"


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
    """

    cmd = build_hydra_command(
        case_path,
        overrides,
    )

    click.echo("Running Hydra:")

    click.echo(" ".join(cmd))

    click.echo()

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

        return exp_dir

    except subprocess.CalledProcessError as exc:
        raise click.ClickException("Hydra run failed " f"({exc.returncode})") from exc


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------
@click.command("build")
@click.argument(
    "target",
    required=False,
)
@click.argument(
    "overrides",
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
    "--dry-run",
    is_flag=True,
    help=("Generate trials only; " "do not execute."),
)
def cmd_build(
    target,
    overrides,
    view,
    markdown,
    latex,
    progress,
    dry_run,
):
    """
    Display available cases and build experiments.

    Examples:
      roost build
      roost build 0
      roost build case.toml
      roost build 0 solver_options.maxSpending=145
    """

    schema_registry = build_registry()
    metrics_registry = build_metrics_registry()
    display_registry = build_display_registry(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
    )

    # ----------------------------------------
    # Discover + load case dataset
    # ----------------------------------------
    ds = attach_row_ids(load_cases("."))
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
    if not target:
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
    selected_row = resolve_case_selection(
        target,
        ds,
    )

    case_path = Path(selected_row["_path"]).resolve()

    click.echo(f"ID   : {selected_row['_row_id']}")

    click.echo(f"Path : {case_path}\n")

    # ----------------------------------------
    # Launch Hydra build
    # ----------------------------------------
    exp_dir = run_hydra_build(
        case_path,
        list(overrides),
    )

    # ----------------------------------------
    # Dry-run exit
    # ----------------------------------------
    if dry_run:
        click.echo("\nDry run complete.\n")

        return

    # ----------------------------------------
    # Discover generated runs
    # ----------------------------------------
    runs = find_runs(exp_dir)

    if not runs:
        click.echo("No runs discovered " "after Hydra build.")

        return

    click.echo()

    click.echo(f"Discovered " f"{len(runs)} runs.")

    # ----------------------------------------
    # Execute runs sequentially
    # ----------------------------------------
    execute_runs(
        runs,
        progress=progress,
    )
