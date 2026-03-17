from __future__ import annotations

import json
import statistics
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import click
import numpy as np
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
@click.option("--view", default="audit_dashboard")
@click.option("--run", "run_id", type=int, help="Re-run runtime row")
@click.option("--export", "export_id", type=int, help="Export runtime row")
@click.option("--open-folder", "open_id", type=int, help="Open trial folder by runtime row")
def cmd_audit(experiment_id, view, run_id, export_id, open_id):
    console = Console()

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

    if experiment_id is None:
        if view == "runtime":
            render_runtime_view(console, experiments, run_id, export_id, open_id)
            return

        render_registry_view(console, experiments, view)
        return

    if experiment_id < 0 or experiment_id >= len(experiments):
        console.print("[red]Invalid experiment ID.[/red]")
        sys.exit(1)

    exp = experiments[experiment_id]

    if view == "runtime":
        render_runtime_view(console, [exp], run_id, export_id, open_id)
    else:
        render_experiment_detail(console, exp)


# =========================================================
# Discovery
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
                            trials.append(
                                Trial(
                                    path=trial_dir,
                                    status=get_trial_status(trial_dir),
                                    runtime=extract_runtime(trial_dir),
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
# Trial Helpers
# =========================================================


def get_trial_status(trial_dir: Path) -> str:
    if (trial_dir / "SOLVED").exists():
        return "SOLVED"
    if (trial_dir / "UNSUCCESSFUL").exists():
        return "FAILED"
    return "INCOMPLETE"


def extract_runtime(trial_dir: Path) -> float | None:
    metrics = next(trial_dir.glob("*_metrics.*"), None)
    if not metrics:
        return None
    try:
        with metrics.open() as f:
            data = json.load(f)
        return data.get("timing", {}).get("elapsed_seconds")
    except Exception:
        return None


# =========================================================
# Registry View
# =========================================================


def render_registry_view(console, experiments, view):
    if view not in VIEW_REGISTRY:
        console.print(f"[red]Unknown view '{view}'[/red]")
        return

    audit_rows = []

    for exp in experiments:
        m = compute_experiment_metrics(exp)
        audit_rows.append(
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
            )
        )

    column_keys = VIEW_REGISTRY[view]
    rows = build_rows(audit_rows, column_keys)

    table = Table(title="ROOST Experiment Audit", box=box.SIMPLE)
    table.add_column("ID", justify="right")

    for key in column_keys:
        col = COLUMN_REGISTRY[key]
        table.add_column(col.label, justify=col.align)

    for idx, row in enumerate(rows):
        out = [str(idx)]
        for key in column_keys:
            col = COLUMN_REGISTRY[key]
            out.append(format_value(row[key], col.fmt))
        table.add_row(*out)

    console.print(table)


# =========================================================
# Runtime View
# =========================================================


def render_runtime_view(console, experiments, run_id=None, export_id=None, open_id=None):
    runtime_rows = []

    # Build rows
    if len(experiments) > 1:
        for exp in experiments:
            for run in exp.runs:
                vals = [t.runtime for t in run.trials if t.runtime]
                if vals:
                    runtime_rows.append(
                        (max(vals), exp.case, exp.date, exp.time, run.name, run.path)
                    )
    else:
        exp = experiments[0]
        for run in exp.runs:
            for trial in run.trials:
                if trial.runtime:
                    runtime_rows.append((trial.runtime, run.name, trial.path))

    if not runtime_rows:
        console.print("[yellow]No runtime data found.[/yellow]")
        return

    runtime_rows = sorted(runtime_rows, reverse=True)

    # ---------------------------------------------------------
    # Determine action
    # ---------------------------------------------------------
    action_id = None
    action_type = None

    if run_id is not None:
        action_id = run_id
        action_type = "run"
    elif export_id is not None:
        action_id = export_id
        action_type = "export"
    elif open_id is not None:
        action_id = open_id
        action_type = "open"

    if action_id is not None:
        if action_id < 0 or action_id >= len(runtime_rows):
            console.print("[red]Invalid ID[/red]")
            return

        selected = runtime_rows[action_id]

        if len(experiments) > 1:
            _, _, _, _, _, path = selected
            trial_path = path
        else:
            _, _, trial_path = selected

        # -----------------------------------------
        # Execute action
        # -----------------------------------------
        if action_type == "open":
            open_in_file_explorer(trial_path)
            console.print(f"[cyan]Opened folder:[/cyan] {trial_path}")

        elif action_type == "run":
            rerun_trial(console, trial_path)

        elif action_type == "export":
            export_trial(console, trial_path)

        return

    # ---------------------------------------------------------
    # Display
    # ---------------------------------------------------------

    table = Table(title="Runtime Analysis", box=box.SIMPLE)
    table.add_column("ID", justify="right")
    table.add_column("TIME (s)", justify="right")
    table.add_column("INFO")

    for idx, row in enumerate(runtime_rows[:20]):
        if len(row) == 6:
            table.add_row(str(idx), f"{row[0]:.3f}", f"{row[1]} {row[4]}")
        else:
            table.add_row(str(idx), f"{row[0]:.3f}", str(row[2]))

    console.print(table)


# =========================================================
# Actions
# =========================================================


def json_safe(obj):
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (datetime | date)):
        return obj.isoformat()
    if isinstance(obj, np.generic):
        return obj.item()
    if hasattr(obj, "__dict__"):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def rerun_trial(console, trial_path: Path):
    import json
    import os
    import time
    from contextlib import contextmanager
    from pathlib import Path

    import owlplanner as owl
    import pandas as pd

    # If you already have this utility, keep using it
    from owlroost.core.metrics_from_plan import write_metrics_json

    # -----------------------------------------
    # Helper: temporary working directory
    # -----------------------------------------
    @contextmanager
    def chdir(path: Path):
        old = Path.cwd()
        try:
            os.chdir(path)
            yield
        finally:
            os.chdir(old)

    # -----------------------------------------
    # Locate effective TOML
    # -----------------------------------------
    toml = next(trial_path.glob("*_effective.toml"), None)

    if not toml:
        console.print("[red]No _effective.toml found[/red]")
        return

    console.print("[bold cyan]Re-running trial[/bold cyan]")
    console.print(f"Path: {trial_path}")
    console.print(f"TOML: {toml.name}\n")

    # -----------------------------------------
    # Execute in trial directory
    # -----------------------------------------
    with chdir(trial_path):
        try:
            # ------------------------------
            # Load plan
            # ------------------------------
            plan = owl.readConfig(
                toml.name,
                logstreams="loguru",
                loadHFP=True,
            )

            # ------------------------------
            # Write rates (match trial_worker)
            # ------------------------------
            rates_dict = {
                "Year": plan.year_n.tolist(),
                "S&P 500": plan.tau_kn[0].tolist(),
                "Corporate Baa": plan.tau_kn[1].tolist(),
                "T Bonds": plan.tau_kn[2].tolist(),
                "inflation": plan.tau_kn[3].tolist(),
            }

            base = Path(toml.stem)  # no suffix
            rates_path = base.with_name(base.stem + "_rates.xlsx")

            pd.DataFrame(rates_dict).to_excel(
                rates_path,
                index=False,
                sheet_name="Rates",
            )

            # ------------------------------
            # Timing wrapper
            # ------------------------------
            start_time = time.time()
            start_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(start_time))

            plan.solve(plan.objective, dict(plan.solverOptions))

            end_time = time.time()
            end_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(end_time))

            elapsed_seconds = end_time - start_time

            timing = {
                "solve_start": start_iso,
                "solve_end": end_iso,
                "elapsed_seconds": elapsed_seconds,
            }

            console.print(f"[cyan]Case status:[/cyan] {plan.caseStatus}")
            console.print(f"[yellow]Rerun time:[/yellow] {elapsed_seconds:.3f}s")

            if plan.caseStatus != "solved":
                return

            # ------------------------------
            # Save results workbook
            # ------------------------------
            results_file = base.with_name(base.stem + "_results.xlsx")

            plan.saveWorkbook(
                basename=results_file.name,  # IMPORTANT: filename only
                overwrite=True,
                with_config="no",
            )

            console.print(f"[green]Saved:[/green] {results_file.name}")

            # ------------------------------
            # Metrics JSON
            # ------------------------------
            metrics_path = base.with_name(base.stem + "_metrics.json")

            write_metrics_json(plan, metrics_path, timing)

            # ------------------------------
            # Summary JSON
            # ------------------------------
            summary_path = base.with_name(base.stem + "_summary.json")

            with open(summary_path, "w") as f:
                json.dump(
                    plan.summaryDic(),
                    f,
                    indent=2,
                    sort_keys=False,
                    default=json_safe,
                )

            console.print(f"[green]Metrics:[/green] {metrics_path.name}")
            console.print(f"[green]Summary:[/green] {summary_path.name}")

        except Exception as e:
            console.print(f"[red]Error during rerun:[/red] {e}")


def export_trial(console, trial_path: Path):
    import zipfile

    # -----------------------------------------
    # Build safe filename from full path
    # -----------------------------------------
    parts = trial_path.parts

    # Optional: drop leading "." or absolute root
    if parts[0] == ".":
        parts = parts[1:]

    # Convert to safe name
    safe_name = "__".join(parts)

    zip_name = f"export__{safe_name}.zip"

    export_dir = Path("exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    zip_path = export_dir / zip_name

    # -----------------------------------------
    # Create zip
    # -----------------------------------------
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in trial_path.rglob("*"):
            if file.is_file():
                # Preserve relative structure inside zip
                arcname = file.relative_to(trial_path)
                zf.write(file, arcname)

    console.print(f"[green]Exported:[/green] {zip_path}")


# =========================================================
# Metrics
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


def render_experiment_detail(console: Console, exp: Experiment):
    console.print()
    console.print(f"[bold cyan]Experiment {exp.id}[/bold cyan]")
    console.print(f"Case: {exp.case}")
    console.print(f"Date: {exp.date}  Time: {exp.time}")
    console.print()

    table = Table(
        header_style="bold cyan",
        box=box.SIMPLE,
        show_edge=False,
    )

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
