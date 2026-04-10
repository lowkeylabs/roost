# src/owlroost/hydra/trial_worker.py

import json
import subprocess
import sys
import tomllib
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from loguru import logger

from owlroost.core.longevity import sample_individual_lifetime


def run_trial_star(args):
    from owlroost.hydra.trial_worker import run_trial

    return run_trial(*args)


def run_single_case_subprocess(args: dict):
    result = subprocess.run(
        [sys.executable, "-m", "owlroost.entrypoints.run_case"],
        input=json.dumps(args),
        text=True,
        capture_output=True,
    )
    logger.trace(f"\n----Full result from subprocess---\n{result}")
    # --------------------------------------------------
    # Hard crash (non-zero exit)
    # --------------------------------------------------
    if result.returncode != 0:
        return SimpleNamespace(
            status="crashed",
            stderr=result.stderr,
        )

    # --------------------------------------------------
    # Empty output (very common failure mode)
    # --------------------------------------------------
    if not result.stdout.strip():
        return SimpleNamespace(
            status="crashed",
            stderr="empty stdout",
        )

    # --------------------------------------------------
    # JSON parse failure
    # --------------------------------------------------
    try:
        data = json.loads(result.stdout)
        return SimpleNamespace(**data)
    except Exception as e:
        return SimpleNamespace(
            status="crashed",
            stderr=f"invalid json: {e}",
        )


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

    # print( f"Before run_single_case_subprocess: {args}" )
    result = run_single_case_subprocess(args)
    # print( f"after run_single_case_subprocess: {result}" )

    if result.status == "crashed":
        logger.debug(f"Trial {trial_id} crashed")

        # --------------------------------------------------
        # Failure classification
        # --------------------------------------------------
        failure_detail = getattr(result, "stderr", "") or "unknown"

        if "empty stdout" in failure_detail:
            failure_category = "empty_output"
        elif "invalid json" in failure_detail:
            failure_category = "invalid_output"
        else:
            failure_category = "worker_crash"

        # --------------------------------------------------
        # Write FAILED marker
        # --------------------------------------------------
        (trial_dir / "FAILED").touch()

        # --------------------------------------------------
        # Write robust fallback metrics.json
        # --------------------------------------------------
        metrics_path = trial_dir / f"{case_file.stem}_metrics.json"

        minimal_metrics = {
            "schema": "roost.metrics.v2",
            # ----------------------------------------------
            # Identity
            # ----------------------------------------------
            "identity": {
                "plan_name": case_file.stem,
            },
            # ----------------------------------------------
            # Run status (CRITICAL)
            # ----------------------------------------------
            "run_status": {
                "status": "failed",
                "failure_category": failure_category,
                "failure_detail": failure_detail,
            },
            # ----------------------------------------------
            # Timing
            # ----------------------------------------------
            "timing": {
                "elapsed_seconds": None,
            },
            # ----------------------------------------------
            # Solver
            # ----------------------------------------------
            "solver": "unknown",
            # ----------------------------------------------
            # Financial (safe minimal structure)
            # ----------------------------------------------
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
            # ----------------------------------------------
            # Risk (safe minimal structure)
            # ----------------------------------------------
            "risk": {
                "scenario": {
                    "valid": False,
                },
                "outcome": {
                    "valid": False,
                },
            },
            # ----------------------------------------------
            # Complexity
            # ----------------------------------------------
            "complexity": {
                "valid": False,
            },
            # ----------------------------------------------
            # Score (optional but safe)
            # ----------------------------------------------
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
            "status": "crashed",
            "output": None,
        }

    return {
        "trial_id": trial_id,
        "rates_seed": rates_seed,
        "longevity_seed": longevity_seed,
        "status": result.status,
        "output": str(output_file) if result.status == "solved" else None,
    }
