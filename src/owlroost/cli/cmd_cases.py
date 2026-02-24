from dataclasses import asdict, is_dataclass
from pathlib import Path

import click
from loguru import logger
from rich import box
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from owlroost.cli.utils import (
    find_case_files,
    index_case_files,
    resolve_case_selector,
)
from owlroost.core.case_upgrade import case_upgrade
from owlroost.domain.case import Case
from owlroost.domain.formatting import format_value
from owlroost.domain.registry import COLUMN_REGISTRY, VIEW_REGISTRY
from owlroost.domain.views import build_rows

UPGRADE_MESSAGES = {
    "longevity_added": "Added [longevity] section",
    "roost_added": "Added [roost] section",
    "longevity_fixed_alignment": "Fixed [longevity] alignment",
    "cache_updated": "Rebuild [cache] section",
}


@click.command(name="cases")
@click.argument("selector", nargs=-1)
@click.option(
    "--view",
    default="basic",
    help="View name (basic, assets, optimization, all)",
)
@click.option(
    "--upgrade",
    is_flag=True,
    help="Upgrade selected cases to ROOST-compatible structure.",
)
@click.option(
    "--set",
    "mutations",
    multiple=True,
    help="Modify case parameter (e.g., --set longevity.sex=male)",
)
@click.option(
    "--apply",
    is_flag=True,
    help="Apply changes to disk. Default is preview only.",
)
def cmd_cases(selector, view, upgrade, mutations, apply):
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

    # --------------------------------------------
    # Mutation Mode (explicit --set only)
    # --------------------------------------------

    if mutations:
        if len(paths) != 1:
            console.print("[red]Mutation requires exactly one selected case.[/red]")
            return

        case = Case(paths[0])

        console.print("[bold cyan]Mutation Preview[/bold cyan]\n")

        try:
            for m in mutations:
                console.print(f"→ {escape(m)}")
                case.apply_mutation(m)

            if apply:
                case.write()
                console.print("\n✓ Changes written to disk.")
            else:
                console.print("\n→ Preview only (use --apply to write).")

        except Exception as e:
            console.print(f"[red]Mutation failed:[/red] {e}")

        return

    # --------------------------------------------
    # If exactly one case selected
    # --------------------------------------------

    if len(paths) == 1 and upgrade:
        case = Case(paths[0])

        console.print("[bold cyan]Upgrade Preview[/bold cyan]\n")

        actions = case_upgrade(case, write=False)

        try:
            case.generate_cache(write=False)
            actions["cache_updated"] = True
        except Exception as e:
            console.print(f"[red]Cache rebuild failed:[/red] {e}")
            actions["cache_updated"] = False

        if apply and any(v for k, v in actions.items() if k != "written"):
            case.write()
            actions["written"] = True

        meaningful_actions = {k: v for k, v in actions.items() if k != "written" and v}

        if meaningful_actions:
            console.print(f"[yellow]{case.filename}[/yellow]")
            for key in meaningful_actions:
                message = UPGRADE_MESSAGES.get(key, key)
                console.print(f"  ✓ {escape(message)}")

            if apply:
                console.print("  → Changes written to disk.\n")
            else:
                console.print("  → Preview only (use --apply to write).\n")
        else:
            console.print("Case already up-to-date.")

        return

    # --------------------------------------------
    # Multiple cases selected
    # --------------------------------------------

    cases = [Case(p) for p in paths]

    if upgrade:
        console.print("[bold cyan]Upgrade Preview[/bold cyan]\n")

        any_changes = False

        for case in cases:
            actions = case_upgrade(case, write=False)

            # Always rebuild cache during upgrade
            try:
                case.generate_cache(write=False)
                actions["cache_updated"] = True
            except Exception as e:
                console.print(f"[red]Cache rebuild failed:[/red] {e}")
                actions["cache_updated"] = False

            # Write once at end if apply
            if apply and any(v for k, v in actions.items() if k != "written"):
                case.write()
                actions["written"] = True

            meaningful_actions = {k: v for k, v in actions.items() if k != "written" and v}

            if meaningful_actions:
                any_changes = True
                console.print(f"[yellow]{case.filename}[/yellow]")

                for key in meaningful_actions:
                    message = UPGRADE_MESSAGES.get(key, key)
                    console.print(f"  ✓ {escape(message)}")

                if apply:
                    console.print("  → Changes written to disk.\n")
                else:
                    console.print("  → Preview only (use --apply to write).\n")

        if not any_changes:
            console.print("All cases already up-to-date.")

        return

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

    table.add_column("ID", justify="right")

    for key in column_keys:
        col = COLUMN_REGISTRY[key]
        table.add_column(col.label, justify=col.align)

    for idx, row in enumerate(rows):
        formatted_row = [str(idx)]

        for key in column_keys:
            col = COLUMN_REGISTRY[key]
            raw_value = row[key]
            formatted = format_value(raw_value, col.fmt)
            formatted_row.append(formatted)

        table.add_row(*formatted_row)

    console.print(table)


# =========================================================
# Single Case Display
# =========================================================


def _display_single_case(console: Console, case: Case):
    console.print(f"\nCASE: {case.name}")
    console.print(f"FILE: {case.filename}")
    console.print("-" * 60)
    console.print(case.professional_summary, width=70)
    console.print()

    # ---------------------------------------------------------
    # Render core OWL sections
    # ---------------------------------------------------------

    config = case.config

    if hasattr(config, "model_dump"):
        config_dict = config.model_dump()
    elif hasattr(config, "dict"):
        config_dict = config.dict()
    elif is_dataclass(config):
        config_dict = asdict(config)
    else:
        config_dict = config

    for section_name, section_value in config_dict.items():
        _render_section(console, section_name, section_value)

    # ---------------------------------------------------------
    # Render ROOST extension sections
    # ---------------------------------------------------------

    if case.extensions:
        for name, model in case.extensions.items():
            if hasattr(model, "model_dump"):
                section_dict = model.model_dump(exclude_none=True)
            else:
                section_dict = model.dict()

            _render_section(console, name, section_dict)


def _render_section(console, name, value, indent=0):
    indent_str = " " * indent

    header_text = escape(f"[{name}]")
    console.print(f"\n{indent_str}[bold cyan]{header_text}[/bold cyan]")

    if is_dataclass(value):
        value = asdict(value)

    if isinstance(value, dict):
        for key, val in value.items():
            _render_field(console, key, val, indent + 2)
    else:
        formatted = format_value(value, None)
        console.print(f"{indent_str}  {formatted}")


def _render_field(console, key, value, indent):
    indent_str = " " * indent

    if isinstance(value, dict):
        _render_section(console, key, value, indent)
        return

    if is_dataclass(value):
        _render_section(console, key, asdict(value), indent)
        return

    fmt = None

    if key in COLUMN_REGISTRY:
        fmt = COLUMN_REGISTRY[key].fmt
    elif key == "generic":
        fmt = "allocation"

    formatted = format_value(value, fmt)

    console.print(f"{indent_str}{key} = {formatted}")
