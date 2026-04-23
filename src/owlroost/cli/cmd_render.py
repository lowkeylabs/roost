from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import click
import yaml
from rich.console import Console

from owlroost.domain.services.discovery import discover_experiments
from owlroost.domain.services.query import apply_filters, apply_sort, apply_top
from owlroost.domain.services.rows import build_run_rows

RESULTS_DIR = Path("results")
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


def resolve_runs(run_rows, experiments, ids):
    resolved = []

    for i in ids:
        if i < 0 or i >= len(run_rows):
            raise click.ClickException(f"Invalid run id {i}")

        row = run_rows[i]
        ref = row["_ref"]

        exp = experiments[ref["exp_index"]]
        run = exp.runs[ref["run_index"]]

        resolved.append(
            {
                "run_id": i,
                "path": str(Path(run.path)),
            }
        )

    return resolved


def resolve_case_name(experiments, run_rows, run_ids):
    cases = set()

    for i in run_ids:
        row = run_rows[i]
        ref = row["_ref"]
        exp = experiments[ref["exp_index"]]
        cases.add(getattr(exp, "case", "unknown"))

    return cases.pop() if len(cases) == 1 else "multi-case"


def resolve_template(template: str) -> Path:
    """
    Resolve template from:
    - explicit path
    - or templates/ directory
    """
    p = Path(template)

    if p.exists():
        return p.resolve()

    candidate = TEMPLATES_DIR / template
    if candidate.exists():
        return candidate.resolve()

    raise click.ClickException(f"Template not found: {template}")


def make_bundle_dir(case: str, template_name: str) -> Path:
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H-%M-%S")

    bundle = REPORTS_DIR / case / template_name / date / time
    bundle.mkdir(parents=True, exist_ok=False)

    return bundle, date, time


# =========================================================
# CLI
# =========================================================


@click.command(name="render")
@click.argument("ids", required=False)
@click.option("--template", required=True, help="Template name or path")
@click.option("--mode", type=click.Choice(["single", "compare", "batch"]), default=None)
@click.option("--case", "case_override", type=int)
@click.option("--experiment", "--exp", "exp_override", type=int)
@click.option("--filter", "filters", multiple=True)
@click.option("--sort", type=str)
@click.option("--top", type=int)
def cmd_render(
    ids,
    template,
    mode,
    case_override,
    exp_override,
    filters,
    sort,
    top,
):
    """
    Create a report bundle:
      - resolves runs
      - snapshots template
      - writes metadata.yaml

    Does NOT generate QMD or run Quarto.
    """
    console = Console()

    if not RESULTS_DIR.exists():
        raise click.ClickException("Results directory not found")

    if not TEMPLATES_DIR.exists():
        raise click.ClickException("Templates directory not found")

    experiments = discover_experiments(RESULTS_DIR)

    # ---------------------------------------------------------
    # Apply filters (same semantics as inspect)
    # ---------------------------------------------------------
    if case_override is not None:
        experiments = [e for e in experiments if getattr(e, "case_id", None) == case_override]

    if exp_override is not None:
        experiments = [e for e in experiments if getattr(e, "id", None) == exp_override]

    if not experiments:
        raise click.ClickException("No experiments found")

    run_rows = build_run_rows(experiments)

    working = [vars(r) if not isinstance(r, dict) else r for r in run_rows]
    working = apply_filters(working, None, filters)
    working = apply_sort(working, None, sort)
    working = apply_top(working, top)

    # ---------------------------------------------------------
    # Resolve run IDs
    # ---------------------------------------------------------
    if ids:
        run_ids = parse_ids(ids)
    else:
        run_ids = list(range(len(working)))

    if not run_ids:
        raise click.ClickException("No runs selected")

    runs = resolve_runs(run_rows, experiments, run_ids)

    # ---------------------------------------------------------
    # Defaults
    # ---------------------------------------------------------
    if mode is None:
        mode = "single" if len(run_ids) == 1 else "compare"

    template_path = resolve_template(template)
    template_name = template_path.name

    case_name = resolve_case_name(experiments, run_rows, run_ids)

    # ---------------------------------------------------------
    # Create bundle
    # ---------------------------------------------------------
    bundle_dir, date, time = make_bundle_dir(case_name, template_name)

    # ---------------------------------------------------------
    # Snapshot template
    # ---------------------------------------------------------
    local_template = bundle_dir / template_name
    shutil.copy(template_path, local_template)

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------
    metadata = {
        "schema": "roost.report.v1",
        "case": case_name,
        "template": {
            "source": str(template_path),
            "local": template_name,
            "mode": "snapshot",
        },
        "mode": mode,
        "generated_at": datetime.now().isoformat(),
        "bundle": {
            "path": str(bundle_dir),
            "date": date,
            "time": time,
        },
        "runs": runs,
        "selection_debug": {
            "input_ids": ids,
            "filters": list(filters),
            "sort": sort,
            "top": top,
            "case_override": case_override,
            "experiment_override": exp_override,
        },
        "notes": "",
        "outputs": {
            "html": True,
            "pdf": False,
            "pptx": False,
        },
    }

    meta_path = bundle_dir / "metadata.yaml"
    meta_path.write_text(yaml.safe_dump(metadata, sort_keys=False))

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------
    console.print()
    console.print(f"[green]Created report bundle:[/green] {bundle_dir}")
    console.print(f"[bold]Template:[/bold] {template_name}")
    console.print(f"[bold]Mode:[/bold] {mode}")
    console.print(f"[bold]Runs:[/bold] {run_ids}")
    console.print(f"[dim]{meta_path}[/dim]")
    console.print()
