# src/owlroost/hydra/trial_worker.py

import json
import subprocess
import sys
import time
import tomllib
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from loguru import logger

from owlroost.core.longevity import sample_individual_lifetime


def _get_runtime_flag(overrides: dict, key: str, default=None):
    runtime = overrides.get("runtime", {})
    if isinstance(runtime, dict):
        return runtime.get(key, default)
    return default


def _to_bool(v, default=True):
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() == "true"
    return default

def run_trial_star(args):
    from owlroost.hydra.trial_worker import run_trial

    return run_trial(*args)


def _exec_subprocess(args: dict, timeout: int):
    start = time.time()

    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "owlroost.entrypoints.run_case"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,   # capture JSON
            stderr=None,              # stream logs live
            text=True,
        )

        try:
            stdout, _ = proc.communicate(
                input=json.dumps(args),
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            finished = time.time()
            return {
                "mode": "subprocess",
                "timeout": True,
                "stdout": "",
                "stderr": "timeout",
                "elapsed": finished - start,
                "started_at": start,
                "finished_at": finished,
            }

        finished = time.time()

        return {
            "mode": "subprocess",
            "returncode": proc.returncode,
            "stdout": stdout or "",
            "stderr": "",
            "elapsed": finished - start,
            "started_at": start,
            "finished_at": finished,
        }

    except Exception as e:
        finished = time.time()
        return {
            "mode": "subprocess",
            "returncode": 1,
            "stdout": "",
            "stderr": str(e),
            "elapsed": finished - start,
            "started_at": start,
            "finished_at": finished,
        }
                

def _exec_inprocess(args: dict, timeout: int):
    import traceback

    start = time.time()

    try:
        from owlroost.core.owl_runner import run_single_case

        result = run_single_case(**args)

        finished = time.time()

        data = {
            "status": result.status,
            "output_file": result.output_file,
            "summary": result.summary,
            "failure_category": result.failure_category,
            "failure_subtype": result.failure_subtype,
            "failure_detail": result.failure_detail,
        }

        return {
            "mode": "inprocess",
            "returncode": 0,
            "stdout": json.dumps(data),
            "stderr": "",
            "elapsed": finished - start,
            "started_at": start,
            "finished_at": finished,
        }

    except Exception:
        finished = time.time()

        err = traceback.format_exc()
        print("\n=== INPROCESS EXCEPTION ===")
        print(err)
        print("===========================\n")

        return {
            "mode": "inprocess",
            "returncode": 1,
            "stdout": "",
            "stderr": err,
            "elapsed": finished - start,
            "started_at": start,
            "finished_at": finished,
        }
        

def _interpret_execution(raw):
    """
    This is your EXISTING logic from run_single_case_subprocess,
    almost unchanged.
    """

    elapsed = raw["elapsed"]
    start = raw["started_at"]
    finished = raw["finished_at"]
    mode = raw.get("mode")

    # ----------------------------------------
    # Timeout
    # ----------------------------------------
    if raw.get("timeout"):
        return SimpleNamespace(
            status="timeout",
            stderr="timeout",
            elapsed_seconds=elapsed,
            started_at=start,
            finished_at=finished,
            execution_mode=mode,
        )

    # ----------------------------------------
    # Hard crash (non-zero exit)
    # ----------------------------------------
    if raw.get("returncode", 1) != 0:
        return SimpleNamespace(
            status="crashed",
            stderr=raw.get("stderr", ""),
            elapsed_seconds=elapsed,
            started_at=start,
            finished_at=finished,
            execution_mode=mode,
        )

    stdout = raw.get("stdout", "")

    # ----------------------------------------
    # Empty output
    # ----------------------------------------
    if not stdout.strip():
        return SimpleNamespace(
            status="crashed",
            stderr="empty stdout",
            elapsed_seconds=elapsed,
            started_at=start,
            finished_at=finished,
            execution_mode=mode,
        )

    # ----------------------------------------
    # JSON parse
    # ----------------------------------------
    try:
        data = json.loads(stdout)
        return SimpleNamespace(
            **data,
            elapsed_seconds=elapsed,
            started_at=start,
            finished_at=finished,
            execution_mode=mode,
        )
    except Exception as e:
        return SimpleNamespace(
            status="crashed",
            stderr=f"invalid json: {e}",
            elapsed_seconds=elapsed,
            started_at=start,
            finished_at=finished,
            execution_mode=mode,
        )
    

def run_single_case(args: dict, timeout: int = 20, use_subprocess: bool = True):
    if use_subprocess:
        raw = _exec_subprocess(args, timeout)
    else:
        raw = _exec_inprocess(args, timeout)

    return _interpret_execution(raw)



def run_trial(
    job_id: int,
    trial_id: int,
    rates_seed: int | None,
    longevity_seed: int | None,
    case_file: Path,
    base_overrides: dict,
    run_dir: Path,
    master_seed: int,
    longevity_cfg: dict | None = None,
):
    """
    Execute a single stochastic trial.

    Architecture:
    - Rates model selection is Hydra-managed (rates_selection group).
    - Longevity model activation is Hydra-managed (longevity group).
    - Seeds are injected per trial.
    - No legacy ROOST flags.
    - No bootstrap mutation layer.
    """

    longevity_cfg = longevity_cfg or {}
    base_overrides = base_overrides or {}

    # ---------------------------------------------------------
    # Trial directory
    # ---------------------------------------------------------
    trial_dir = run_dir / "trials" / f"{trial_id:04d}"
    trial_dir.mkdir(parents=True, exist_ok=True)

    output_file = trial_dir / f"{case_file.stem}.xlsx"

    # Deep copy to prevent cross-trial mutation
    overrides = deepcopy(base_overrides)

    # ---------------------------------------------------------
    # Inject rate seed (Hydra-managed rates_selection)
    # ---------------------------------------------------------
    if rates_seed is not None:
        rates_override = overrides.setdefault("rates_selection", {})
        rates_override["rate_seed"] = rates_seed
        rates_override["reproducible_rates"] = True

    # ---------------------------------------------------------
    # Determine if longevity group is active
    # ---------------------------------------------------------
    longevity_model_active = "longevity" in overrides

    longevity_runtime = {}
    if longevity_model_active and longevity_seed is not None:
        longevity_runtime["longevity_seed"] = longevity_seed

    # ---------------------------------------------------------
    # Longevity stochastic sampling (Hydra-driven)
    # ---------------------------------------------------------
    if longevity_model_active:
        case_data = tomllib.loads(case_file.read_text())
        ages = case_data["basic_info"]["life_expectancy"]

        case_longevity = case_data.get("longevity", {})
        overrides_longevity = overrides.setdefault("longevity", {})

        # Read apply flag from Hydra overrides or config
        apply_to_plan = longevity_cfg.get("apply_to_plan", False)

        health = case_longevity.get("health", ["average"] * len(ages))
        sex = case_longevity.get("sex", ["female"] * len(ages))
        smoker = case_longevity.get("smoker", [False] * len(ages))

        n_people = len(ages)
        default_partnered = n_people == 2
        partnered = case_longevity.get("partnered", default_partnered)

        rng = np.random.default_rng(longevity_seed)

        sampled_life_exp = [
            int(
                sample_individual_lifetime(
                    rng,
                    current_age=ages[i],
                    health=health[i],
                    sex=sex[i],
                    smoker=smoker[i],
                    partnered=partnered,
                )
            )
            for i in range(len(ages))
        ]

        # Always record runtime metadata
        overrides_longevity.setdefault("model", "default")
        overrides_longevity["health"] = health
        overrides_longevity["sex"] = sex
        overrides_longevity["smoker"] = smoker
        overrides_longevity["partnered"] = partnered
        overrides_longevity["apply_to_plan"] = apply_to_plan

        # ONLY overwrite if enabled
        if apply_to_plan:
            overrides.setdefault("basic_info", {})["life_expectancy"] = sampled_life_exp

        longevity_runtime["base_life_expectancy"] = ages
        longevity_runtime["calculated_life_expectancy"] = sampled_life_exp

    # ---------------------------------------------------------
    # Runtime metadata for effective TOML tracking
    # ---------------------------------------------------------

    roost_cfg = overrides.get("roost", {})
    experiment_name = roost_cfg.get("experiment")
    run_name = run_dir.name

    roost_runtime = {
        "trial_id": trial_id,
        "run_name": run_name,
        "experiment": experiment_name,
        "master_seed": master_seed,
        "rates_seed": rates_seed,
        "longevity_seed": longevity_seed,
    }

    if 0:
        logger.debug(
            "Job: {:5} | Trial {:04d} | overrides={} | rates_seed={} | longevity_seed={} | dir={}",
            job_id,
            trial_id,
            overrides,
            rates_seed if rates_seed is not None else "TOML",
            longevity_seed if longevity_seed is not None else "TOML",
            trial_dir.relative_to(run_dir),
        )

    # ---------------------------------------------------------
    # Execute case
    # ---------------------------------------------------------
    #    if CURRENT_LOG_LEVEL not in {"TRACE", "DEBUG"}:
    #        logger.info("Job: {:5} | Trial {:04d}", job_id, trial_id)

    args = {
        "case_file": str(case_file),
        "overrides": overrides,
        "output_file": str(output_file),
        "roost_runtime": roost_runtime,
        "longevity_runtime": longevity_runtime,
    }

    # --------------------------------------------------
    # PRIMARY WRAPPER AROUND OWL. designed to catch hard fails
    # and solver crashes that prevent _metrics.json from being written.
    # This file is the source of truth for trial status.
    # --------------------------------------------------

    # print( f"Before run_single_case_subprocess: {args}" )

    timeout = _get_runtime_flag(overrides, "worker_timeout", 20)
    use_subprocess = _to_bool(_get_runtime_flag(overrides, "run_owl_as_subprocess", True))
    threads = _get_runtime_flag(overrides, "math_library_threads")

    # Optional: safety guard
    import os
    if "JOBLIB_PARENT_PID" in os.environ:
        use_subprocess = True

    if not use_subprocess:
        logger.debug("In-process execution: worker_timeout not enforced")

    logger.debug(
        "Execution use_subprocess={} timeout={} threads={}",
        use_subprocess,
        timeout,
        threads,
    )

    result = run_single_case(
        args,
        timeout=timeout,
        use_subprocess=use_subprocess,
    )


    # --------------------------------------------------
    # Check for metrics.json existence (SOURCE OF TRUTH)
    # --------------------------------------------------
    metrics_path = trial_dir / f"{case_file.stem}_metrics.json"
    metrics_exists = metrics_path.exists()

    # --------------------------------------------------
    # Extract structured subprocess result (NEW CONTRACT)
    # --------------------------------------------------
    result_status = getattr(result, "status", None)
    result_failure_category = getattr(result, "failure_category", None)
    result_failure_subtype = getattr(result, "failure_subtype", None)
    result_failure_detail = getattr(result, "failure_detail", None)
    result_elapsed_seconds = getattr(result, "elapsed_seconds", None)
    result_started_at = getattr(result, "started_at", None)
    result_finished_at = getattr(result, "finished_at", None)

    raw_stderr = getattr(result, "stderr", "") or ""
    lines = [line.strip() for line in raw_stderr.strip().splitlines() if line.strip()]

    # --------------------------------------------------
    # Determine failure_detail (prefer subprocess)
    # --------------------------------------------------
    failure_detail = result_failure_detail

    if not failure_detail:
        failure_detail = "unknown error"
        if lines:
            for line in reversed(lines):
                if any(k in line for k in ["Error", "Exception", "Traceback"]):
                    failure_detail = line
                    break
            else:
                failure_detail = lines[-1]

    # --------------------------------------------------
    # Detect input/config errors
    # --------------------------------------------------
    input_error_keywords = [
        "TOMLDecodeError",
        "KeyError",
        "ValueError",
        "TypeError",
        "Invalid",
        "missing",
        "unexpected",
    ]

    is_input_error = result_failure_category == "input_error" or any(
        k in raw_stderr for k in input_error_keywords
    )

    # --------------------------------------------------
    # Determine if fallback metrics are required
    # --------------------------------------------------
    needs_fallback = False

    if result_status in ("crashed", "timeout"):
        needs_fallback = True
    elif not metrics_exists:
        needs_fallback = True

    # --------------------------------------------------
    # Handle failure cases
    # --------------------------------------------------
    if needs_fallback:
        logger.debug(f"Trial {trial_id} failed or missing metrics.json")

        # --------------------------------------------------
        # Failure classification (NEW CONTRACT)
        # --------------------------------------------------
        if result_failure_category:
            failure_category = result_failure_category
            failure_subtype = result_failure_subtype

        elif result_status == "timeout":
            failure_category = "timeout"
            failure_subtype = "subprocess_timeout"

        elif is_input_error:
            failure_category = "input_error"
            failure_subtype = "stderr_detected"

        elif "empty stdout" in failure_detail:
            failure_category = "empty_output"
            failure_subtype = None

        elif "invalid json" in failure_detail:
            failure_category = "invalid_output"
            failure_subtype = None

        elif not metrics_exists:
            failure_category = "hard_crash"
            failure_subtype = "no_metrics"

        else:
            failure_category = "worker_crash"
            failure_subtype = None

        # --------------------------------------------------
        # Write FAILED marker
        # --------------------------------------------------
        (trial_dir / "FAILED").touch()

        # --------------------------------------------------
        # Persist stderr for debugging (optional but useful)
        # --------------------------------------------------
        try:
            (trial_dir / "stderr.txt").write_text(raw_stderr)
        except Exception:
            pass

        # --------------------------------------------------
        # Write fallback metrics ONLY if missing
        # --------------------------------------------------
        if not metrics_exists:
            minimal_metrics = {
                "schema": "roost.metrics.v2",
                "identity": {
                    "plan_name": case_file.stem,
                },
                "run_status": {
                    "status": "failed",
                    "failure_category": failure_category,
                    "failure_subtype": failure_subtype,
                    "failure_detail": failure_detail,
                    "failure_stderr": raw_stderr[:2000],
                },
                "timing": {
                    "elapsed_seconds": result_elapsed_seconds,
                },
                "solver": "unknown",
                "financial": {
                    "valid": False,
                    "baseline": {
                        "annual_spending": None,
                    },
                    "timeseries": {
                        "spending": {
                            "ratio": {
                                "min": 0.0,
                                "mean": 0.0,
                                "median": 0.0,
                            }
                        }
                    },
                },
                "risk": {
                    "scenario": {"valid": False},
                    "outcome": {"valid": False},
                },
                "complexity": {"valid": False},
                "score": None,
            }

            try:
                with open(metrics_path, "w") as f:
                    json.dump(minimal_metrics, f, indent=2)
            except Exception:
                logger.exception("Failed to write crash fallback metrics")

        return {
            "trial_id": trial_id,
            "rates_seed": rates_seed,
            "longevity_seed": longevity_seed,
            "status": "failed",
            "output": None,
            "error": failure_detail,
            "elapsed_seconds": result_elapsed_seconds,
            "started_at": result_started_at,
            "finished_at": result_finished_at,
        }

    # --------------------------------------------------
    # Success path
    # --------------------------------------------------
    return {
        "trial_id": trial_id,
        "rates_seed": rates_seed,
        "longevity_seed": longevity_seed,
        "status": result_status or "solved",
        "output": str(output_file),
        "error": None,
        "elapsed_seconds": result_elapsed_seconds,
        "started_at": result_started_at,
        "finished_at": result_finished_at,
    }
