import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from io import StringIO
from pathlib import Path

import click
import owlplanner as owl
import toml

from owlroost.core.metrics_from_plan import write_metrics_json


# ---------------------------------------------------------
# Core: minimal trial execution
# ---------------------------------------------------------
def run_trial_from_toml(trial_dir: Path):
    trial_toml = trial_dir / "trial.toml"

    if not trial_toml.exists():
        raise RuntimeError(f"Missing trial.toml in {trial_dir}")

    # Skip if already done
    if list(trial_dir.glob("metrics.json")):
        return {"status": "skipped", "trial_dir": str(trial_dir)}

    # ----------------------------------------
    # Load TOML
    # ----------------------------------------
    toml_dict = toml.load(trial_toml)
    toml_str = toml.dumps(toml_dict)

    buf = StringIO(toml_str)

    # ----------------------------------------
    # Build + solve
    # ----------------------------------------
    start = time.time()

    plan = owl.readConfig(
        buf,
        logstreams="loguru",
        loadHFP=False,
    )

    plan.solve(plan.objective, plan.solverOptions)

    elapsed = time.time() - start

    # ----------------------------------------
    # Write metrics
    # ----------------------------------------
    # case_name = toml_dict.get("case_name", trial_dir.name)
    metrics_path = trial_dir / "metrics.json"

    timing = {"elapsed_seconds": elapsed}
    write_metrics_json(plan, metrics_path, timing)

    return {
        "status": plan.caseStatus or "unknown",
        "elapsed": elapsed,
        "trial_dir": str(trial_dir),
    }


# ---------------------------------------------------------
# Discovery
# ---------------------------------------------------------
def find_runs(results_root: Path):
    """
    Find all run directories (contain trials/ subdir).
    """
    runs = []

    for trials_dir in results_root.rglob("trials"):
        run_dir = trials_dir.parent
        runs.append(run_dir)

    return sorted(runs)


def summarize_run(run_dir: Path):
    trials_dir = run_dir / "trials"
    trial_dirs = sorted([p for p in trials_dir.iterdir() if p.is_dir()])

    total = len(trial_dirs)
    completed = 0

    for td in trial_dirs:
        if list(td.glob("*_metrics.json")):
            completed += 1

    return {
        "run_dir": run_dir,
        "total": total,
        "completed": completed,
    }


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------
@click.command("run")
@click.option("--root", default="results", type=click.Path(exists=True))
@click.option("--run-all", is_flag=True, help="Run all pending trials")
@click.option("--trial-jobs", default=4, help="Parallel workers")
def cmd_run(root, run_all, trial_jobs):
    """
    List runs and optionally execute pending trials.
    """
    root = Path(root).resolve()

    runs = find_runs(root)

    if not runs:
        click.echo("No runs found.")
        return

    click.echo("\nRuns:\n")

    all_pending = []

    # ----------------------------------------
    # Summarize
    # ----------------------------------------
    for idx, run_dir in enumerate(runs):
        summary = summarize_run(run_dir)

        click.echo(
            f"[{idx:02d}] {run_dir.relative_to(root)} "
            f"| trials: {summary['completed']}/{summary['total']}"
        )

        if run_all:
            trials_dir = run_dir / "trials"
            for td in trials_dir.iterdir():
                if not td.is_dir():
                    continue
                if not list(td.glob("*_metrics.json")):
                    all_pending.append(td)

    # ----------------------------------------
    # Execute if requested
    # ----------------------------------------
    if not run_all:
        return

    if not all_pending:
        click.echo("\nNo pending trials.")
        return

    click.echo(f"\nRunning {len(all_pending)} pending trials...\n")

    results = []

    if trial_jobs == 1:
        for td in all_pending:
            r = run_trial_from_toml(td)
            click.echo(f"{td.name} -> {r['status']}")
            results.append(r)
    else:
        with ProcessPoolExecutor(max_workers=trial_jobs) as ex:
            futures = [ex.submit(run_trial_from_toml, td) for td in all_pending]

            for f in as_completed(futures):
                r = f.result()
                click.echo(f"{Path(r['trial_dir']).name} -> {r['status']}")
                results.append(r)

    # ----------------------------------------
    # Summary
    # ----------------------------------------
    solved = sum(1 for r in results if r["status"] == "solved")
    failed = len(results) - solved

    click.echo(f"\nDone: {solved} solved, {failed} failed\n")


if __name__ == "__main__":
    cmd_run()
