from __future__ import annotations

import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.table import Table

import owlroost.domain.audit_registry  # noqa: F401
from owlroost.cli.utils import open_in_file_explorer
from owlroost.domain.audit import AuditRow
from owlroost.domain.formatting import format_value
from owlroost.domain.registry import COLUMN_REGISTRY, VIEW_REGISTRY
from owlroost.domain.views import build_rows

RESULTS_DIR = Path("results")


# =========================================================
# Data Models
# =========================================================


@dataclass
class Trial:
    path: Path
    status: str
    runtime: float | None = None
    data: dict | None = None


@dataclass
class Run:
    name: str
    path: Path
    trials: list[Trial]


@dataclass
class Experiment:
    id: int
    case: str
    date: str
    time: str
    path: Path
    runs: list[Run]


# =========================================================
# CLI
# =========================================================


@click.command(name="audit")
@click.argument("experiment_id", required=False, type=int)
@click.option("--view", default="dashboard")
@click.option("--run", "run_id", type=int)
@click.option("--export", "export_id", type=int)
@click.option("--open-folder", "open_id", type=int)
def cmd_audit(experiment_id, view, run_id, export_id, open_id):
    console = Console()

    # ---------------------------------------------------------
    # Validate actions
    # ---------------------------------------------------------
    actions = [run_id, export_id, open_id]
    if sum(x is not None for x in actions) > 1:
        console.print("[red]Use only one of --run, --export, or --open-folder[/red]")
        sys.exit(1)

    if not RESULTS_DIR.exists():
        console.print("[red]Results directory not found.[/red]")
        sys.exit(1)

    experiments = discover_experiments()

    if not experiments:
        console.print("[yellow]No experiments found.[/yellow]")
        return

    # ---------------------------------------------------------
    # Validate view
    # ---------------------------------------------------------
    if "audit_" + view not in VIEW_REGISTRY:
        available = ", ".join(VIEW_REGISTRY.keys())
        console.print(f"[red]Unknown view '{view}'. Available: {available}[/red]")
        return

    # ---------------------------------------------------------
    # Single experiment detail
    # ---------------------------------------------------------
    if experiment_id is not None:
        if experiment_id < 0 or experiment_id >= len(experiments):
            console.print("[red]Invalid experiment ID.[/red]")
            sys.exit(1)

        experiments = [experiments[experiment_id]]

    # ---------------------------------------------------------
    # Build rows
    # ---------------------------------------------------------
    audit_rows = build_audit_rows(experiments)

    column_keys = VIEW_REGISTRY["audit_" + view]
    rows = build_rows(audit_rows, column_keys)

    # ---------------------------------------------------------
    # Handle actions (trial-level)
    # ---------------------------------------------------------
    if run_id is not None or export_id is not None or open_id is not None:
        runtime_rows = build_runtime_rows(experiments)

        if not runtime_rows:
            console.print("[yellow]No runtime data available.[/yellow]")
            return

        runtime_rows = sorted(runtime_rows, key=lambda r: r["runtime"], reverse=True)

        action_id = (
            run_id if run_id is not None else export_id if export_id is not None else open_id
        )
        action_type = "run" if run_id is not None else "export" if export_id is not None else "open"

        if action_id < 0 or action_id >= len(runtime_rows):
            console.print("[red]Invalid ID[/red]")
            return

        trial_path = runtime_rows[action_id]["path"]

        if action_type == "open":
            open_in_file_explorer(trial_path)
            console.print(f"[cyan]Opened folder:[/cyan] {trial_path}")

        elif action_type == "run":
            rerun_trial(console, trial_path)

        elif action_type == "export":
            export_trial(console, trial_path)

        return

    # ---------------------------------------------------------
    # Render table (registry-driven)
    # ---------------------------------------------------------
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
            formatted = format_value(row[key], col.fmt)
            formatted_row.append(formatted)

        table.add_row(*formatted_row)

    console.print(table)


# =========================================================
# Row Builders
# =========================================================


def build_audit_rows(experiments: list[Experiment]) -> list[AuditRow]:
    rows = []

    for exp in experiments:
        m = compute_experiment_metrics(exp)
        agg = aggregate_trial_metrics(exp)

        rows.append(
            AuditRow(
                id=exp.id,
                case=exp.case,
                date=exp.date,
                time=exp.time,
                runs=m["runs"],
                trials=m["trials"],
                solved=m["solved"],
                failed=m["failed"],
                incomplete=m["incomplete"],
                slow=m["slow"],
                success_rate=m["success_rate"],
                runtime=agg.get("runtime"),
                spend_basis=agg.get("spend_basis"),
                total_spend_real=agg.get("total_spend_real"),
                bequest_real=agg.get("bequest_real"),
                nvars=agg.get("nvars"),
                ncons=agg.get("ncons"),
                nnz=agg.get("nnz"),
                int_ratio=agg.get("int_ratio"),
            )
        )

    return rows


def build_runtime_rows(experiments):
    rows = []

    for exp in experiments:
        for run in exp.runs:
            for trial in run.trials:
                if trial.runtime:
                    rows.append(
                        {
                            "runtime": trial.runtime,
                            "path": trial.path,
                        }
                    )

    return rows


def aggregate_trial_metrics(exp: Experiment) -> dict:
    def collect(key):
        values = []
        for run in exp.runs:
            for t in run.trials:
                if t.data and t.data.get(key) is not None:
                    values.append(t.data[key])
        return values

    def mean_or_none(values):
        return statistics.mean(values) if values else None

    return dict(
        runtime=mean_or_none(collect("runtime")),
        spend_basis=mean_or_none(collect("spend_basis")),
        total_spend_real=mean_or_none(collect("total_spend_real")),
        bequest_real=mean_or_none(collect("bequest_real")),
        nvars=mean_or_none(collect("nvars")),
        ncons=mean_or_none(collect("ncons")),
        nnz=mean_or_none(collect("nnz")),
        int_ratio=mean_or_none(collect("int_ratio")),
    )


# =========================================================
# Discovery (unchanged)
# =========================================================


def discover_experiments() -> list[Experiment]:
    experiments: list[Experiment] = []
    exp_id = 0

    for case_dir in sorted(p for p in RESULTS_DIR.iterdir() if p.is_dir()):
        for date_dir in sorted(p for p in case_dir.iterdir() if p.is_dir()):
            for time_dir in sorted(p for p in date_dir.iterdir() if p.is_dir()):
                runs: list[Run] = []

                for run_dir in sorted(
                    p for p in time_dir.iterdir() if p.is_dir() and p.name.startswith("run_")
                ):
                    trials: list[Trial] = []
                    trials_dir = run_dir / "trials"

                    if trials_dir.exists():
                        for trial_dir in sorted(p for p in trials_dir.iterdir() if p.is_dir()):
                            data = extract_trial_data(trial_dir)

                            trials.append(
                                Trial(
                                    path=trial_dir,
                                    status=get_trial_status(trial_dir),
                                    runtime=data["runtime"] if data else None,
                                    data=data,
                                )
                            )

                    runs.append(Run(run_dir.name, run_dir, trials))

                experiments.append(
                    Experiment(
                        id=exp_id,
                        case=case_dir.name,
                        date=date_dir.name,
                        time=time_dir.name,
                        path=time_dir,
                        runs=runs,
                    )
                )

                exp_id += 1

    return experiments


# =========================================================
# Trial Helpers (unchanged)
# =========================================================


def get_trial_status(trial_dir: Path) -> str:
    if (trial_dir / "SOLVED").exists():
        return "SOLVED"
    if (trial_dir / "UNSUCCESSFUL").exists():
        return "FAILED"
    return "INCOMPLETE"


def extract_trial_data(trial_dir: Path) -> dict | None:
    metrics_file = next(trial_dir.glob("*_metrics.*"), None)
    if not metrics_file:
        return None

    try:
        with metrics_file.open() as f:
            data = json.load(f)

        metrics = data.get("metrics", {})
        complexity = data.get("complexity", {})
        timing = data.get("timing", {})

        return {
            "runtime": timing.get("elapsed_seconds"),
            "spend_basis": metrics.get("net_yearly_spending_basis"),
            "total_spend_real": metrics.get("total_net_spending_real"),
            "bequest_real": metrics.get("total_final_bequest_real"),
            "nvars": complexity.get("num_decision_variables"),
            "ncons": complexity.get("num_constraints"),
            "nnz": complexity.get("num_nonzeros"),
            "int_ratio": complexity.get("integer_variable_ratio"),
        }

    except Exception:
        return None


# =========================================================
# Metrics (unchanged)
# =========================================================


def compute_experiment_metrics(exp: Experiment):
    trials = []
    solved = failed = incomplete = 0

    for run in exp.runs:
        for trial in run.trials:
            trials.append(trial)
            if trial.status == "SOLVED":
                solved += 1
            elif trial.status == "FAILED":
                failed += 1
            else:
                incomplete += 1

    runtimes = [t.runtime for t in trials if t.runtime]
    slow = 0

    if runtimes:
        median = statistics.median(runtimes)
        slow = sum(1 for r in runtimes if r > 3 * median)

    success_rate = (solved / len(trials) * 100) if trials else 0

    return dict(
        runs=len(exp.runs),
        trials=len(trials),
        solved=solved,
        failed=failed,
        incomplete=incomplete,
        slow=slow,
        success_rate=success_rate,
    )


# =========================================================
# Actions (unchanged)
# =========================================================


def rerun_trial(console, trial_path: Path):
    import os
    import time
    from contextlib import contextmanager

    import owlplanner as owl

    from owlroost.core.metrics_from_plan import write_metrics_json

    @contextmanager
    def chdir(path: Path):
        old = Path.cwd()
        try:
            os.chdir(path)
            yield
        finally:
            os.chdir(old)

    toml = next(trial_path.glob("*_effective.toml"), None)

    if not toml:
        console.print("[red]No _effective.toml found[/red]")
        return

    console.print(f"[bold cyan]Re-running[/bold cyan] {trial_path}")

    with chdir(trial_path):
        try:
            plan = owl.readConfig(toml.name, logstreams="loguru", loadHFP=True)

            start = time.time()
            plan.solve(plan.objective, dict(plan.solverOptions))
            elapsed = time.time() - start

            console.print(f"[cyan]Status:[/cyan] {plan.caseStatus}")
            console.print(f"[yellow]Time:[/yellow] {elapsed:.3f}s")

            if plan.caseStatus != "solved":
                return

            base = Path(toml.stem)

            plan.saveWorkbook(
                basename=(base.stem + "_results.xlsx"),
                overwrite=True,
                with_config="no",
            )

            write_metrics_json(
                plan,
                base.with_name(base.stem + "_metrics.json"),
                {"elapsed_seconds": elapsed},
            )

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


def export_trial(console, trial_path: Path):
    import zipfile

    safe_name = "__".join(trial_path.parts)
    zip_path = Path("exports") / f"export__{safe_name}.zip"
    zip_path.parent.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in trial_path.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(trial_path))

    console.print(f"[green]Exported:[/green] {zip_path}")


# =========================================================
# Detail View (unchanged)
# =========================================================


def render_experiment_detail(console: Console, exp: Experiment):
    console.print(f"[bold cyan]Experiment {exp.id}[/bold cyan]")
    console.print(f"Case: {exp.case}")
    console.print(f"Date: {exp.date}  Time: {exp.time}\n")

    table = Table(box=box.SIMPLE)

    table.add_column("RUN")
    table.add_column("TRIALS", justify="right")
    table.add_column("SOLVED", justify="right")
    table.add_column("FAILED", justify="right")
    table.add_column("SLOW", justify="right")
    table.add_column("SUCCESS %", justify="right")

    for run in exp.runs:
        runtimes = [t.runtime for t in run.trials if t.runtime]

        slow = 0
        if runtimes:
            median = statistics.median(runtimes)
            slow = sum(1 for r in runtimes if r > 3 * median)

        trials = len(run.trials)
        solved = sum(1 for t in run.trials if t.status == "SOLVED")
        failed = sum(1 for t in run.trials if t.status == "FAILED")

        success_rate = (solved / trials * 100) if trials else 0

        table.add_row(
            run.name,
            str(trials),
            str(solved),
            str(failed),
            str(slow),
            f"{success_rate:.1f}",
        )

    console.print(table)
