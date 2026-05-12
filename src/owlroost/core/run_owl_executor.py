# src/owlroost/core/run_owl_executor.py

from __future__ import annotations

import time
import tomllib
from concurrent.futures import (
    ProcessPoolExecutor,
    as_completed,
)
from io import StringIO
from pathlib import Path

import click
import owlplanner as owl
import toml
from loguru import logger

from owlroost.core.progress_renderers import (
    create_renderer,
)
from owlroost.display.discovery import (
    find_trials,
    has_metrics,
    summarize_run,
)
from owlroost.metrics.builders import (
    write_metrics_json,
)

__all__ = [
    "run_trial_from_toml",
    "index_runs",
    "resolve_run_selection",
    "load_run_config",
    "extract_trial_jobs",
    "execute_trials",
    "execute_run",
    "execute_runs",
    "render_run_summary",
    "render_execution_summary",
]


# =========================================================
# Trial execution
# =========================================================
def run_trial_from_toml(
    trial_dir: Path,
):
    """
    Execute a single trial.toml.
    """

    trial_dir = Path(trial_dir)

    trial_toml = trial_dir / "trial.toml"

    if not trial_toml.exists():
        raise RuntimeError("Missing trial.toml in " f"{trial_dir}")

    # ----------------------------------------
    # Skip completed trials
    # ----------------------------------------
    if has_metrics(trial_dir):
        return {
            "status": "skipped",
            "trial_dir": str(trial_dir),
        }

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

    plan.solve(
        plan.objective,
        plan.solverOptions,
    )

    elapsed = time.time() - start

    # ----------------------------------------
    # Write metrics
    # ----------------------------------------
    metrics_path = trial_dir / "metrics.json"

    timing = {"elapsed_seconds": elapsed}

    write_metrics_json(
        plan,
        metrics_path,
        timing,
    )

    return {
        "status": (plan.caseStatus or "unknown"),
        "elapsed": elapsed,
        "trial_dir": str(trial_dir),
    }


# =========================================================
# Run indexing / selection
# =========================================================
def index_runs(
    runs,
):
    """
    Attach integer IDs to run list.
    """

    out = []

    for idx, run_dir in enumerate(runs):
        out.append(
            {
                "id": idx,
                "path": Path(run_dir),
            }
        )

    return out


def resolve_run_selection(
    args,
    indexed_runs,
):
    """
    Resolve CLI run selections
    into run paths.
    """

    selected = []

    for arg in args:
        if not arg.isdigit():
            raise click.ClickException(f"Invalid run ID: {arg}")

        idx = int(arg)

        if idx < 0 or idx >= len(indexed_runs):
            raise click.ClickException(f"Invalid run ID: {idx}")

        selected.append(indexed_runs[idx]["path"])

    return selected


# =========================================================
# Run config
# =========================================================
def load_run_config(
    run_dir: Path,
):
    """
    Load run.toml.
    """

    run_toml = Path(run_dir) / "run.toml"

    if not run_toml.exists():
        raise RuntimeError(f"Missing run.toml: {run_toml}")

    with open(run_toml, "rb") as f:
        return tomllib.load(f)


def extract_trial_jobs(
    run_cfg,
    default=1,
):
    """
    Extract runtime.trial_jobs.
    """

    runtime = run_cfg.get(
        "runtime",
        {},
    )

    return int(
        runtime.get(
            "trial_jobs",
            default,
        )
    )


# =========================================================
# Rendering
# =========================================================
def render_run_summary(
    indexed_runs,
    root,
):
    """
    Render run summary list.
    """

    click.echo("\nRuns:\n")

    for item in indexed_runs:
        idx = item["id"]

        run_dir = item["path"]

        summary = summarize_run(run_dir)

        click.echo(
            f"[{idx:02d}] "
            f"{run_dir.relative_to(root)} "
            f"| trials: "
            f"{summary['completed']}"
            f"/{summary['total']}"
        )

    click.echo()


def render_execution_summary(
    results,
):
    """
    Render execution totals.
    """

    solved = sum(1 for r in results if r["status"] == "solved")

    failed = len(results) - solved

    click.echo(f"\nDone: " f"{solved} solved, " f"{failed} failed\n")


# =========================================================
# Execution
# =========================================================
def execute_trials(
    pending_trials,
    trial_jobs=1,
    progress="rich",
    desc="Trials",
):
    """
    Execute pending trials.
    """

    if not pending_trials:
        click.echo("\nNo pending trials.\n")

        return []

    click.echo(
        f"\nRunning " f"{len(pending_trials)} " f"pending trials " f"with {trial_jobs} workers...\n"
    )

    results = []

    renderer = create_renderer(
        progress,
        desc=desc,
    )

    renderer.start(len(pending_trials))

    try:
        # ------------------------------------
        # Sequential
        # ------------------------------------
        if trial_jobs == 1:
            for td in pending_trials:
                try:
                    r = run_trial_from_toml(td)

                except Exception as exc:
                    logger.exception("Trial execution failed")

                    r = {
                        "status": "failed",
                        "error": str(exc),
                        "trial_dir": str(td),
                    }

                results.append(r)

                renderer.advance(
                    1,
                    len(results),
                    len(pending_trials),
                )

        # ------------------------------------
        # Parallel
        # ------------------------------------
        else:
            with ProcessPoolExecutor(max_workers=trial_jobs) as ex:
                futures = {
                    ex.submit(
                        run_trial_from_toml,
                        td,
                    ): td
                    for td in pending_trials
                }

                for f in as_completed(futures):
                    td = futures[f]

                    try:
                        r = f.result()

                    except Exception as exc:
                        logger.exception("Trial execution failed")

                        r = {
                            "status": "failed",
                            "error": str(exc),
                            "trial_dir": str(td),
                        }

                    results.append(r)

                    renderer.advance(
                        1,
                        len(results),
                        len(pending_trials),
                    )

    finally:
        renderer.finish()

    return results


# =========================================================
# Run-level execution
# =========================================================
def execute_run(
    run_dir,
    progress="rich",
):
    """
    Execute all pending trials
    for a single run.
    """

    run_dir = Path(run_dir)

    run_cfg = load_run_config(run_dir)

    trial_jobs = extract_trial_jobs(
        run_cfg,
    )

    pending_trials = [td for td in find_trials(run_dir) if not has_metrics(td)]

    click.echo()

    click.echo(f"Run: {run_dir.name}")

    click.echo(f"trial_jobs={trial_jobs}")

    click.echo(f"pending_trials={len(pending_trials)}")

    start = time.time()

    results = execute_trials(
        pending_trials,
        trial_jobs=trial_jobs,
        progress=progress,
        desc=(f"{run_dir.name} " f"({trial_jobs} workers)"),
    )

    elapsed = time.time() - start

    for r in results:
        r["run_dir"] = str(run_dir)

    click.echo(f"run_elapsed={elapsed:.1f}s")

    render_execution_summary(results)

    return results


def execute_runs(
    run_dirs,
    progress="rich",
):
    """
    Execute runs sequentially.
    """

    all_results = []

    for run_dir in run_dirs:
        results = execute_run(
            run_dir,
            progress=progress,
        )

        all_results.extend(results)

    click.echo()

    click.echo(f"Completed {len(run_dirs)} runs.")

    render_execution_summary(all_results)

    return all_results
