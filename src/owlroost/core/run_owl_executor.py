# src/owlroost/core/run_owl_executor.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

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


def validate_execution_plan(run_dirs):
    required_solvers = set()

    for run_dir in run_dirs:
        cfg = load_run_config(run_dir)

        solver = cfg.get("roost_runtime", {}).get("resolved_solver")

        if solver:
            required_solvers.add(solver)

    # -------------------------------------------------
    # MOSEK validation
    # -------------------------------------------------

    if "MOSEK" in required_solvers:
        if not mosek_available():
            raise RuntimeError(
                "\n"
                "Execution plan requires MOSEK, but MOSEK "
                "is unavailable.\n\n"
                "Required by one or more runs.\n"
                "Verify:\n"
                "  - mosek Python package installed\n"
                "  - MOSEKLM_LICENSE_FILE configured\n"
            )


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
        raise RuntimeError(f"Missing trial.toml in {trial_dir}")

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

    # click.echo()


def render_execution_summary(
    results,
):
    """
    Render execution totals.
    """

    solved = sum(1 for r in results if r["status"] == "solved")

    _failed = len(results) - solved


#    click.echo(f"\nDone: " f"{solved} solved, " f"{failed} failed\n")


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
            f"\nRunning {len(pending_trials)} pending trials with {workers_per_run} workers...\n"
        )

    results = []

    renderer = create_renderer(progress, desc=desc) if progress != "none" else None

    if renderer:
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

                if renderer:
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

                    if renderer:
                        renderer.advance(
                            1,
                            len(results),
                            len(pending_trials),
                        )

    finally:
        if renderer:
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
        solver = run_cfg["roost_runtime"]["resolved_solver"]
        workers_per_run = run_cfg["roost_runtime"]["resolved_workers_per_run"]

        case_name = run_cfg.get("case", {}).get("name")

        if not case_name:
            case_name = run_dir.parent.name

        label = f"{case_name}/{run_dir.name}"

        label_width = int(
            os.environ.get(
                "OWLROOST_PROGRESS_LABEL_WIDTH",
                len(label),
            )
        )

        label = f"{label:<{label_width}}"

        desc = f"{label} ({workers_per_run} workers, {solver})"

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
        click.echo("WARNING: run timing does not include all trials (partial execution)")

    #    render_execution_summary(results)

    return results


# =========================================================
# Execute ALL runs
# =========================================================


def execute_runs(
    run_dirs,
    progress="rich",
    rerun: bool = False,
):
    """
    Execute runs using hybrid scheduling:

    - runs with trials_per_run == 1
      are bundled and executed in parallel

    - runs with trials_per_run > 1
      are executed sequentially because
      they already internally parallelize

    Bundled single-trial runs use the
    workers_per_run value resolved from
    the first bundled run.
    """

    run_dirs = [Path(r) for r in run_dirs]
    if not run_dirs:
        return []

    # =========================================================
    # Global execution validation
    # =========================================================

    validate_execution_plan(run_dirs)

    # =====================================================
    # Classify runs
    # =====================================================

    single_trial_runs = []

    multi_trial_runs = []

    for run_dir in run_dirs:
        run_cfg = load_run_config(run_dir)

        runtime = run_cfg.get(
            "roost_runtime",
            {},
        )

        trials_per_run = int(
            runtime.get(
                "trials_per_run",
                1,
            )
        )

        if trials_per_run == 1:
            single_trial_runs.append(run_dir)

        else:
            multi_trial_runs.append(run_dir)

    # =====================================================
    # Summary
    # =====================================================

    # logger.info(
    #    "Execution plan: "
    #    f"{len(single_trial_runs)} bundled single-trial runs, "
    #    f"{len(multi_trial_runs)} multi-trial runs"
    # )

    all_results = []

    # =====================================================
    # Phase 1:
    # Bundled single-trial runs
    # =====================================================

    if single_trial_runs:
        first_cfg = load_run_config(single_trial_runs[0])

        bundled_workers = first_cfg.get("roost_runtime", {}).get("resolved_workers_per_run", 1)

        # logger.info("Executing bundled single-trial runs " f"with {bundled_workers} workers")

        renderer = create_renderer(
            progress,
            desc="Bundled single-trial runs",
        )

        renderer.start(len(single_trial_runs))

        try:
            with ProcessPoolExecutor(
                max_workers=bundled_workers,
            ) as ex:
                futures = {
                    ex.submit(
                        execute_run,
                        run_dir,
                        progress="none",
                        rerun=rerun,
                    ): run_dir
                    for run_dir in single_trial_runs
                }

                completed = 0

                for future in as_completed(futures):
                    run_dir = futures[future]

                    try:
                        results = future.result()

                    except Exception:
                        logger.exception(f"Run failed: {run_dir}")

                        results = [
                            {
                                "status": "failed",
                                "run_dir": str(run_dir),
                            }
                        ]

                    all_results.extend(results)

                    completed += 1

                    renderer.advance(
                        1,
                        completed,
                        len(single_trial_runs),
                    )

        finally:
            renderer.finish()

    # =====================================================
    # Phase 2:
    # Multi-trial runs
    # =====================================================

    for run_dir in multi_trial_runs:
        # logger.info(f"Executing multi-trial run: {run_dir.name}")

        results = execute_run(
            run_dir,
            progress=progress,
            rerun=rerun,
        )

        all_results.extend(results)

    # =====================================================
    # Summary
    # =====================================================

    render_execution_summary(all_results)

    return all_results
