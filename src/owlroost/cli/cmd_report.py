from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import click
import yaml
from rich.console import Console

REPORTS_DIR = Path("reports")
TEMPLATES_DIR = Path("templates")


# =========================================================
# Helpers
# =========================================================


def parse_ids(arg: str) -> list[int]:
    ids = set()

    for part in arg.split(","):
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = int(start_str)
            end = int(end_str)
            ids.update(range(start, end + 1))
        else:
            ids.add(int(part))

    return sorted(ids)


def discover_bundles(root: Path):
    bundles = []

    if not root.exists():
        return bundles

    for case_dir in root.iterdir():
        if not case_dir.is_dir():
            continue

        for template_dir in case_dir.iterdir():
            for date_dir in template_dir.iterdir():
                for time_dir in date_dir.iterdir():
                    meta = time_dir / "metadata.yaml"
                    if meta.exists():
                        bundles.append(time_dir)

    return sorted(bundles)


def select_bundles(bundles, ids):
    if ids is None:
        return bundles

    selected = []
    for i in ids:
        if i < 0 or i >= len(bundles):
            raise click.ClickException(f"Invalid report id {i}")
        selected.append(bundles[i])

    return selected


def load_metadata(bundle: Path):
    meta_path = bundle / "metadata.yaml"
    if not meta_path.exists():
        raise click.ClickException(f"Missing metadata.yaml in {bundle}")

    return yaml.safe_load(meta_path.read_text())


def resolve_template(meta, bundle: Path) -> Path:
    t = meta["template"]

    if t.get("mode") == "snapshot":
        return bundle / t["local"]
    else:
        return Path(t["source"])


# =========================================================
# Freshen (QMD generation)
# =========================================================


def freshen_bundle(bundle: Path, console: Console):
    meta = load_metadata(bundle)
    template_path = resolve_template(meta, bundle)

    if not template_path.exists():
        raise click.ClickException(f"Template not found: {template_path}")

    index_qmd = bundle / "index.qmd"

    # copy template → index.qmd
    shutil.copy(template_path, index_qmd)

    # inject minimal header
    header = [
        "---",
        f"title: 'ROOST Report ({meta.get('case')})'",
        "format: html",
        "---",
        "",
    ]

    content = index_qmd.read_text()
    index_qmd.write_text("\n".join(header) + content)

    console.print(f"[green]  freshened[/green] {index_qmd}")


# =========================================================
# Quarto runner
# =========================================================


def run_quarto(bundle: Path, console: Console):
    try:
        subprocess.run(
            ["quarto", "render", str(bundle)],
            check=True,
        )
        console.print(f"[green]  rendered[/green] {bundle}")
    except Exception as e:
        raise click.ClickException(f"Quarto failed: {e}") from None


# =========================================================
# Template promotion
# =========================================================


def promote_template(bundle: Path, console: Console, new_name: str | None, overwrite: bool):
    meta = load_metadata(bundle)

    local_template = resolve_template(meta, bundle)

    if not local_template.exists():
        raise click.ClickException("No local template found in bundle")

    if new_name:
        target = TEMPLATES_DIR / new_name
    else:
        original = Path(meta["template"]["source"]).name
        target = TEMPLATES_DIR / original

    if target.exists() and not overwrite:
        raise click.ClickException(f"{target} exists (use --overwrite or --as)")

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(local_template, target)

    console.print(f"[green]Promoted template → {target}[/green]")


# =========================================================
# CLI
# =========================================================


@click.command(name="report")
@click.argument("ids", required=False)
@click.option("--freshen", is_flag=True, help="Generate QMD artifacts from metadata")
@click.option("--run-quarto", is_flag=True, help="Run Quarto render on bundles")
@click.option("--promote", is_flag=True, help="Promote template to central store")
@click.option("--as", "new_name", type=str, help="New template name when promoting")
@click.option("--overwrite", is_flag=True, help="Overwrite template when promoting")
def cmd_report(ids, freshen, run_quarto_flag, promote, new_name, overwrite):
    """
    Manage and build report bundles.

    Default: list bundles
    """
    console = Console()

    bundles = discover_bundles(REPORTS_DIR)

    if not bundles:
        console.print("[yellow]No report bundles found[/yellow]")
        return

    id_list = parse_ids(ids) if ids else None
    selected = select_bundles(bundles, id_list)

    # ---------------------------------------------------------
    # Default: list
    # ---------------------------------------------------------
    if not freshen and not run_quarto_flag and not promote:
        console.print()
        console.print("[bold]Report Bundles[/bold]\n")

        for i, b in enumerate(bundles):
            console.print(f"{i:>3}  {b}")

        console.print()
        return

    # ---------------------------------------------------------
    # Process selected bundles
    # ---------------------------------------------------------
    for i, bundle in enumerate(selected):
        console.print(f"[bold]Bundle {i}: {bundle}[/bold]")

        if freshen:
            freshen_bundle(bundle, console)

        if run_quarto_flag:
            run_quarto(bundle, console)

        if promote:
            promote_template(bundle, console, new_name, overwrite)

    console.print()
