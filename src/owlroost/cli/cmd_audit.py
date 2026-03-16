from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.table import Table

RESULTS_DIR = Path("results")


# =========================================================
# Data Models
# =========================================================


@dataclass
class Trial:
    path: Path
    status: str


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
def cmd_audit(experiment_id):
    """
    Audit ROOST experiment results.
    """

    console = Console()

    if not RESULTS_DIR.exists():
        console.print("[red]Results directory not found.[/red]")
        sys.exit(1)

    experiments = discover_experiments()

    if not experiments:
        console.print("[yellow]No experiments found.[/yellow]")
        return

    if experiment_id is None:
        render_dashboard(console, experiments)
        return

    if experiment_id < 0 or experiment_id >= len(experiments):
        console.print("[red]Invalid experiment ID.[/red]")
        sys.exit(1)

    render_experiment_detail(console, experiments[experiment_id])


# =========================================================
# Discovery
# =========================================================


def discover_experiments() -> list[Experiment]:
    experiments: list[Experiment] = []

    exp_id = 0

    for case_dir in sorted(p for p in RESULTS_DIR.iterdir() if p.is_dir()):
        case_name = case_dir.name

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
                                )
                            )

                    runs.append(
                        Run(
                            name=run_dir.name,
                            path=run_dir,
                            trials=trials,
                        )
                    )

                experiments.append(
                    Experiment(
                        id=exp_id,
                        case=case_name,
                        date=date_dir.name,
                        time=time_dir.name,
                        path=time_dir,
                        runs=runs,
                    )
                )

                exp_id += 1

    return experiments


# =========================================================
# Trial Status
# =========================================================


def get_trial_status(trial_dir: Path) -> str:
    if (trial_dir / "SOLVED").exists():
        return "SOLVED"

    if (trial_dir / "UNSUCCESSFUL").exists():
        return "FAILED"

    return "INCOMPLETE"


# =========================================================
# Metrics
# =========================================================


def compute_experiment_metrics(exp: Experiment):
    runs = len(exp.runs)

    trials = 0
    solved = 0
    failed = 0
    incomplete = 0

    for run in exp.runs:
        for trial in run.trials:
            trials += 1

            if trial.status == "SOLVED":
                solved += 1
            elif trial.status == "FAILED":
                failed += 1
            else:
                incomplete += 1

    success_rate = (solved / trials * 100) if trials else 0

    return {
        "runs": runs,
        "trials": trials,
        "solved": solved,
        "failed": failed,
        "incomplete": incomplete,
        "success_rate": success_rate,
    }


# =========================================================
# Dashboard View
# =========================================================


def render_dashboard(console: Console, experiments: list[Experiment]):
    table = Table(
        title="ROOST Experiment Audit",
        header_style="bold cyan",
        box=box.SIMPLE,
        show_edge=False,
    )

    table.add_column("ID", justify="right")
    table.add_column("CASE")
    table.add_column("DATE")
    table.add_column("TIME")
    table.add_column("RUNS", justify="right")
    table.add_column("TRIALS", justify="right")
    table.add_column("SOLVED", justify="right")
    table.add_column("FAILED", justify="right")
    table.add_column("INCOMPLETE", justify="right")
    table.add_column("SUCCESS %", justify="right")

    for exp in experiments:
        m = compute_experiment_metrics(exp)

        table.add_row(
            str(exp.id),
            exp.case,
            exp.date,
            exp.time,
            str(m["runs"]),
            str(m["trials"]),
            str(m["solved"]),
            str(m["failed"]),
            str(m["incomplete"]),
            f"{m['success_rate']:.1f}",
        )

    console.print(table)


# =========================================================
# Experiment Detail View
# =========================================================


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
    table.add_column("INCOMPLETE", justify="right")
    table.add_column("SUCCESS %", justify="right")

    for run in exp.runs:
        trials = len(run.trials)
        solved = sum(1 for t in run.trials if t.status == "SOLVED")
        failed = sum(1 for t in run.trials if t.status == "FAILED")
        incomplete = sum(1 for t in run.trials if t.status == "INCOMPLETE")

        success_rate = (solved / trials * 100) if trials else 0

        table.add_row(
            run.name,
            str(trials),
            str(solved),
            str(failed),
            str(incomplete),
            f"{success_rate:.1f}",
        )

    console.print(table)

    console.print()

    console.print(
        "[dim]Tip: future versions of 'roost audit' will include failure diagnostics and repair tools.[/dim]"
    )
