# src/owlroost/core/run_owl_executor.py

from __future__ import annotations

import importlib.util
import json
import os
import time
import tomllib
from concurrent.futures import (
    ProcessPoolExecutor,
    as_completed,
)
from contextlib import contextmanager
from datetime import datetime
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
    "resolve_workers_per_run",
    "resolve_solver_name",
    "execute_trials",
    "execute_run",
    "execute_runs",
    "render_run_summary",
    "render_execution_summary",
]


def mosek_available():
    return (
        importlib.util.find_spec("mosek") is not None
        and os.environ.get("MOSEKLM_LICENSE_FILE") is not None
    )


def resolve_solver_name(run_cfg):
    solver = run_cfg.get(
        "solver_options",
        {},
    ).get(
        "solver",
        "default",
    )

    if solver == "default":
        return "MOSEK" if mosek_available() else "HiGHS"

    return solver


# =========================================================
# Trial execution
# =========================================================
def run_trial_from_toml(
    trial_dir: Path,
    rerun: bool = False,
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
    logger.debug(f"rerun={rerun}")
    if has_metrics(trial_dir) and not rerun:
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


def resolve_workers_per_run(
    run_cfg,
    default=1,
):
    """
    Resolve workers_per_run using either:

    - explicit fixed value
    - solver-aware auto tuning
    """

    runtime = run_cfg.get(
        "roost_runtime",
        {},
    )

    solver = resolve_solver_name(run_cfg)

    mode = runtime.get(
        "workers_per_run_mode",
        "fixed",
    )

    # -----------------------------------------------------
    # Fixed mode
    # -----------------------------------------------------

    if mode == "fixed":
        return int(
            runtime.get(
                "workers_per_run",
                default,
            )
        )

    # -----------------------------------------------------
    # Auto mode
    # -----------------------------------------------------

    if mode == "auto":
        mapping = runtime.get(
            "auto_workers_by_solver",
            {},
        )

        if solver in mapping:
            return int(mapping[solver])

        return int(
            runtime.get(
                "workers_per_run",
                default,
            )
        )

    raise ValueError(f"Unknown workers_per_run_mode: {mode}")


@contextmanager
def runtime_environment_scope(
    run_cfg,
):
    """
    Temporarily apply runtime_environment
    variables for a run.

    Worker processes inherit this environment.

    Original environment is restored afterward.
    """

    runtime_env = run_cfg.get(
        "runtime_environment",
        {},
    )

    managed_vars = set(runtime_env.keys())

    # ----------------------------------------
    # Save originals
    # ----------------------------------------

    original_env = {key: os.environ.get(key) for key in managed_vars}

    try:
        # ------------------------------------
        # Clear managed vars first
        # ------------------------------------

        for key in managed_vars:
            os.environ.pop(
                key,
                None,
            )

        # ------------------------------------
        # Apply run-specific vars
        # ------------------------------------

        if runtime_env:
            for key, value in runtime_env.items():
                if value is None:
                    continue
                os.environ[key] = str(value)
                logger.debug(f"RUNTIME ENV: {key}={value}")

        yield

    finally:
        # ------------------------------------
        # Remove run-specific values
        # ------------------------------------

        for key in managed_vars:
            os.environ.pop(
                key,
                None,
            )

        # ------------------------------------
        # Restore originals
        # ------------------------------------

        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value


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
    workers_per_run: int = 1,
    progress="rich",
    desc="Trials",
    rerun: bool = False,
):
    """
    Execute pending trials.
    """

    if not pending_trials:
        click.echo("\nNo pending trials.\n")

        return []

    if 0:
        click.echo(
            f"\nRunning "
            f"{len(pending_trials)} "
            f"pending trials "
            f"with {workers_per_run} workers...\n"
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
        if workers_per_run == 1:
            for td in pending_trials:
                try:
                    r = run_trial_from_toml(td, rerun=rerun)

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
            with ProcessPoolExecutor(max_workers=workers_per_run) as ex:
                futures = {
                    ex.submit(
                        run_trial_from_toml,
                        td,
                        rerun=rerun,
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
    rerun: bool = False,
):
    """
    Execute all pending trials
    for a single run.
    """

    run_dir = Path(run_dir)

    run_cfg = load_run_config(run_dir)

    workers_per_run = resolve_workers_per_run(run_cfg)

    all_trials = find_trials(run_dir)

    pending_trials = [td for td in all_trials if rerun or not has_metrics(td)]

    #    click.echo()
    #    click.echo(f"Run: {run_dir.name}")
    #    click.echo(f"workers_per_run={workers_per_run}")
    #    click.echo(f"Rerun flag={rerun}")
    #    click.echo(f"pending_trials={len(pending_trials)}")

    # ----------------------------------------
    # Timing validity
    # ----------------------------------------

    timing_is_whole = rerun or len(pending_trials) == len(all_trials)

    # ----------------------------------------
    # Execute
    # ----------------------------------------

    started_at = datetime.now()

    start = time.time()

    with runtime_environment_scope(run_cfg):
        solver = resolve_solver_name(run_cfg)

        desc = f"{run_dir.name} " f"({workers_per_run} workers, {solver})"

        results = execute_trials(
            pending_trials,
            workers_per_run=workers_per_run,
            progress=progress,
            desc=desc,
            rerun=rerun,
        )

    elapsed = time.time() - start

    finished_at = datetime.now()

    # ----------------------------------------
    # Attach run_dir
    # ----------------------------------------

    for r in results:
        r["run_dir"] = str(run_dir)

    # ----------------------------------------
    # Timing summary
    # ----------------------------------------

    completed_trials = sum(1 for r in results if r.get("status") not in ("failed",))

    failed_trials = sum(1 for r in results if r.get("status") == "failed")

    skipped_trials = sum(1 for r in results if r.get("status") == "skipped")

    timing_payload = {
        "run_timing": {
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "elapsed_seconds": elapsed,
            "timing_is_whole": timing_is_whole,
        },
        "run_execution": {
            "workers_per_run": workers_per_run,
            "total_trials": len(all_trials),
            "pending_trials": len(pending_trials),
            "executed_trials": len(results),
            "completed_trials": completed_trials,
            "failed_trials": failed_trials,
            "skipped_trials": skipped_trials,
            "rerun": rerun,
        },
    }

    # ----------------------------------------
    # Save timing artifact
    # ----------------------------------------

    timing_path = run_dir / "run_timing.json"

    with open(
        timing_path,
        "w",
    ) as f:
        json.dump(
            timing_payload,
            f,
            indent=2,
        )

    # ----------------------------------------
    # Console output
    # ----------------------------------------

    #   click.echo(vf"run_elapsed={elapsed:.1f}s" )

    if not timing_is_whole:
        click.echo("WARNING: run timing does not include all trials " "(partial execution)")

    #    render_execution_summary(results)

    return results


# =========================================================
# Execute ALL runs
# =========================================================


def execute_runs(
    run_dirs,
    progress="rich",
    rerun: bool = True,
):
    """
    Execute runs sequentially.
    """

    all_results = []

    for run_dir in run_dirs:
        results = execute_run(
            run_dir,
            progress=progress,
            rerun=rerun,
        )

        all_results.extend(results)

    click.echo()

    click.echo(f"Completed {len(run_dirs)} runs.")

    render_execution_summary(all_results)

    return all_results
