# src/owlroost/hydra/trial_worker.py

import tomllib
from pathlib import Path

import numpy as np
from loguru import logger

from owlroost.core.configure_logging import CURRENT_LOG_LEVEL
from owlroost.core.longevity import sample_individual_lifetime
from owlroost.core.owl_runner import run_single_case


def run_trial_star(args):
    from owlroost.hydra.trial_worker import run_trial

    return run_trial(*args)


def run_trial(
    job_id: int,
    trial_id: int,
    rates_seed: int | None,
    longevity_seed: int | None,
    case_file: Path,
    base_overrides: dict,
    run_dir: Path,
):
    trial_dir = run_dir / "trials" / f"{trial_id:04d}"
    trial_dir.mkdir(parents=True, exist_ok=True)

    output_file = trial_dir / f"{case_file.stem}.xlsx"
    overrides = dict(base_overrides)

    # ---------------------------------------------------------
    # Rates seed
    # ---------------------------------------------------------
    if rates_seed is not None:
        rates_override = overrides.setdefault("rates", {})
        rates_override["rate_seed"] = rates_seed
        rates_override["reproducible_rates"] = True

    # ---------------------------------------------------------
    # Longevity model
    # ---------------------------------------------------------
    case_data = tomllib.loads(case_file.read_text())
    use_longevity_model = case_data.get("roost", {}).get(
        "use_longevity_model", False
    )

    use_bootstrap_model = case_data.get("roost", {}).get(
        "use_bootstrap_model", False
    )

    if use_bootstrap_model:
        rates_override = overrides.setdefault("rates", {})
        rates_override.update({
            "method": "bootstrap_sor",
            "bootstrap_type": "block",
            "block_size": 7,
            "frm": 1928,
            "to" : 2025,
        })

    if use_longevity_model:
        # Ages from base case
        ages = case_data["basic_info"]["life_expectancy"]

        # Longevity model parameters (from [longevity] section)
        longevity_section = case_data.get("longevity", {})

        health = longevity_section.get("health", ["average"] * len(ages))
        sex = longevity_section.get("sex", ["female"] * len(ages))
        smoker = longevity_section.get("smoker", [False] * len(ages))

        n_people = len(ages)
        default_partnered = n_people == 2
        partnered = longevity_section.get("partnered", default_partnered)

        rng = np.random.default_rng(longevity_seed)

        life_exp = [
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

        # Override deterministic life expectancy in basic_info
        overrides.setdefault("basic_info", {})["life_expectancy"] = life_exp

        # Store longevity seed in overrides
        overrides.setdefault("longevity", {})["longevity_seed"] = longevity_seed

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
    if CURRENT_LOG_LEVEL not in {"TRACE", "DEBUG"}:
        logger.info(
            "Job: {:5} | Trial {:04d}",
            job_id,
            trial_id,
        )

    result = run_single_case(
        case_file=str(case_file),
        overrides=overrides,
        output_file=str(output_file),
    )

    return {
        "trial_id": trial_id,
        "rates_seed": rates_seed,
        "longevity_seed": longevity_seed,
        "status": result.status,
        "output": str(output_file) if result.status == "solved" else None,
    }
