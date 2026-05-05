import subprocess
import sys
from pathlib import Path

import click

from owlroost.display import load_cases
from owlroost.display.api import render


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def _with_ids(dataset):
    rows = []
    for i, r in enumerate(dataset.rows):
        new = dict(r)
        new["_row_id"] = i
        rows.append(new)
    return type(dataset)(rows, level=dataset.level)


def _resolve_selection(arg, dataset):
    rows = dataset.rows

    # ID
    if arg.isdigit():
        idx = int(arg)
        if idx < 0 or idx >= len(rows):
            raise click.ClickException(f"Invalid ID: {idx}")
        return rows[idx]

    # File path
    path = Path(arg)
    if not path.exists():
        raise click.ClickException(f"File not found: {arg}")

    for r in rows:
        if Path(r["_path"]).resolve() == path.resolve():
            return r

    raise click.ClickException(f"File not recognized as case: {arg}")


def _inject_id_column(table, dataset):
    table.columns = ["ID"] + list(table.columns)

    new_rows = []
    for row_data, r in zip(table.rows, dataset.rows, strict=False):
        new_rows.append([str(r["_row_id"])] + list(row_data))

    table.rows = new_rows
    return table


# ---------------------------------------------------------
# Hydra execution
# ---------------------------------------------------------
def _run_hydra(case_path: Path, overrides: list[str]):
    """
    Execute Hydra generator in multirun mode.
    """

    # locate package root (same approach as old system)
    package_root = Path(__file__).parents[1]
    conf_dir = package_root / "conf"

    cmd = [
        sys.executable,
        "-m",
        "owlroost.hydra.generate_trials",
        # 🔥 CRITICAL
        "--multirun",
        # 🔥 REQUIRED for Hydra to find your generated config
        f"--config-path={conf_dir}",
        "--config-name=config",
        # inputs
        f"case.file={str(case_path)}",
        f"case.name={case_path.stem}",
    ]

    cmd.extend(overrides)

    click.echo("Running Hydra:")
    click.echo(" ".join(cmd))
    click.echo()

    result = subprocess.run(cmd)

    if result.returncode != 0:
        raise click.ClickException("Hydra run failed")


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------
@click.command("build")
@click.argument("target", required=False)
@click.argument("overrides", nargs=-1)
@click.option("--view", default="basic")
@click.option("--markdown", is_flag=True)
@click.option("--latex", is_flag=True)
def cmd_build(target, overrides, view, markdown, latex):
    """
    Display cases and build experiments

    Examples:
      roost build
      roost build 0
      roost build case.toml
      roost build 0 solver_options.maxSpending=145
    """

    # ----------------------------------------
    # Load dataset
    # ----------------------------------------
    ds = _with_ids(load_cases("."))

    renderer = "rich"
    if markdown:
        renderer = "markdown"
    elif latex:
        renderer = "latex"

    # ----------------------------------------
    # No target → LIST
    # ----------------------------------------
    if not target:
        table = ds.view(view)
        table = _inject_id_column(table, ds)

        output = render(table, renderer)
        if output:
            click.echo(output)
        return

    # ----------------------------------------
    # Resolve target
    # ----------------------------------------
    selected_row = _resolve_selection(target, ds)
    case_path = Path(selected_row["_path"]).resolve()

    click.echo(f"ID   : {selected_row['_row_id']}")
    click.echo(f"Path : {case_path}\n")

    # ----------------------------------------
    # ALWAYS run hydra if target provided
    # ----------------------------------------
    _run_hydra(case_path, list(overrides))
