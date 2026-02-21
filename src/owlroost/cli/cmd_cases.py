from pathlib import Path

import click
from loguru import logger
from rich import box
from rich.console import Console
from rich.table import Table

from owlroost.cli.utils import (
    find_case_files,
    index_case_files,
    resolve_case_selector,
)
from owlroost.domain.case import Case
from owlroost.domain.formatting import format_value
from owlroost.domain.registry import COLUMN_REGISTRY, VIEW_REGISTRY
from owlroost.domain.views import build_rows


@click.command(name="cases")
@click.argument("selector", nargs=-1)
@click.option(
    "--view",
    default="basic",
    help="View name (basic, assets, optimization, all)",
)
def cmd_cases(selector, view):
    console = Console()

    directory = Path(".")
    logger.debug(f"Scanning directory: {directory}")

    files = find_case_files(directory)

    if not files:
        console.print("No .toml case files found.")
        return

    indexed_files = index_case_files(files)

    # --------------------------------------------
    # Resolve cases
    # --------------------------------------------

    if selector:
        paths = []
        for sel in selector:
            match = resolve_case_selector(sel, indexed_files)
            if not match:
                console.print(f"[red]No case matching '{sel}'[/red]")
                return
            paths.append(match)
    else:
        paths = files

    cases = [Case(p) for p in paths]

    # --------------------------------------------
    # Resolve view
    # --------------------------------------------

    if view not in VIEW_REGISTRY:
        available = ", ".join(VIEW_REGISTRY.keys())
        console.print(f"[red]Unknown view '{view}'. Available: {available}[/red]")
        return

    column_keys = VIEW_REGISTRY[view]
    rows = build_rows(cases, column_keys)

    if not rows:
        return

    # --------------------------------------------
    # Build Rich table
    # --------------------------------------------

    table = Table(
        header_style="bold cyan",
        row_styles=["none", "none"],
        box=box.SIMPLE,
        show_header=True,
        show_edge=False,
        show_lines=False,
    )

    # Add columns using registry metadata
    for key in column_keys:
        col = COLUMN_REGISTRY[key]
        table.add_column(col.label, justify=col.align)

    # Add rows
    for row in rows:
        formatted_row = []

        for key in column_keys:
            col = COLUMN_REGISTRY[key]
            raw_value = row[key]
            formatted = format_value(raw_value, col.fmt)
            formatted_row.append(formatted)

        table.add_row(*formatted_row)

    console.print(table)
