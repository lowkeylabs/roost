# src/owlroost/hydra/owl_hydra_run.py

import time
from multiprocessing import Pool

import hydra
import numpy as np
from hydra.core.hydra_config import HydraConfig
from loguru import logger
from omegaconf import DictConfig
from tqdm import tqdm

from owlroost.cli.utils import normalize_case_file_overrides
from owlroost.core.configure_logging import configure_logging
from owlroost.core.override_parser import hydra_overrides_to_dict
from owlroost.hydra.helpers import (
    PROJECT_ROOT,
    bootstrap_logging,
    get_job_id,
    get_run_dir,
    register_resolvers,
    resolve_case_file,
    save_hydra_metadata,
)
from owlroost.hydra.trial_worker import run_trial

# ---------------------------------------------------------------------
# Bootstrap (must run before Hydra initializes)
# ---------------------------------------------------------------------
bootstrap_logging()
register_resolvers()


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------
def fits_uint32(n: int) -> bool:
    return 0 <= n <= 0xFFFFFFFF


def _extract_trial_override(overrides: dict, key: str, default: int | None = None):
    """Extract integer overrides from CLI parsed dict structure."""
    try:
        return int(overrides.get("trial", {}).get(key, default))
    except Exception:
        return default


def get_master_seed(cfg: DictConfig, job_id: str) -> int:
    """
    Resolve master_seed with precedence:
      1) Case TOML [ROOST].master_seed
      2) Hydra config roost.master_seed
    """

    source = None

    case_roost = getattr(cfg.case, "ROOST", None)
    if case_roost and hasattr(case_roost, "master_seed"):
        master_seed = int(case_roost.master_seed)
        source = "case"
    elif hasattr(cfg, "roost") and hasattr(cfg.roost, "master_seed"):
        master_seed = int(cfg.roost.master_seed)
        source = "hydra"
    else:
        raise RuntimeError(
            "master_seed must be defined either in case [ROOST] "
            "or in Hydra config (roost.master_seed)"
        )

    if not fits_uint32(master_seed):
        raise ValueError(f"Invalid master_seed (must fit uint32): {master_seed}")

    logger.info("{} - Using master_seed={} (source={})", job_id, master_seed, source)

    return master_seed


# ---------------------------------------------------------------------
# MAIN HYDRA ENTRYPOINT
# ---------------------------------------------------------------------
@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig):
    # -----------------------------------------
    # Validate required inputs
    # -----------------------------------------
    if not hasattr(cfg, "case") or not hasattr(cfg.case, "file"):
        raise RuntimeError("Hydra config must define case.file")

    case_file = resolve_case_file(cfg.case.file)

    # Configure logging per Hydra
    configure_logging(cfg)

    # Hydra runtime and overrides
    hc = HydraConfig.get()
    raw_overrides = hc.overrides.task
    job_id = get_job_id(hc)

    overrides = hydra_overrides_to_dict(raw_overrides)
    clean_overrides = normalize_case_file_overrides(raw_overrides)

    logger.debug("{} - overrides: {}", job_id, " ".join(clean_overrides))

    run_dir = get_run_dir()
    logger.debug("{} - Run directory: {}", job_id, run_dir.relative_to(PROJECT_ROOT))

    # -----------------------------------------
    # Master seed (universe-level)
    # -----------------------------------------
    master_seed = get_master_seed(cfg, job_id)

    save_hydra_metadata(
        run_dir=run_dir,
        mode=hc.mode,
        job_id=job_id,
        overrides=raw_overrides,
        extra={"master_seed": master_seed},
    )

    # -----------------------------------------
    # Trial configuration
    # -----------------------------------------
    trial_cfg = cfg.trial
    n_jobs = int(trial_cfg.n_jobs)

    trial_id_override = _extract_trial_override(overrides, "id")
    trial_count_override = _extract_trial_override(overrides, "count", default=int(trial_cfg.count))

    use_trial_seeds = trial_id_override is not None or trial_count_override > 1

    trial_args = []

    # ---------------------------------------------------------
    # Determine trial IDs
    # ---------------------------------------------------------
    if trial_id_override is not None:
        trial_ids = [trial_id_override]
    elif trial_count_override == 1:
        trial_ids = [0]
    else:
        trial_ids = list(range(trial_count_override))

    # ---------------------------------------------------------
    # Deterministic seed generation per trial
    # ---------------------------------------------------------
    for tid in trial_ids:
        rates_seed = None
        longevity_seed = None

        if use_trial_seeds:
            # Deterministic per-trial seed hierarchy
            trial_ss = np.random.SeedSequence(master_seed, spawn_key=(tid,))
            rs, ls = trial_ss.spawn(2)

            rates_seed = int(rs.generate_state(1)[0])
            longevity_seed = int(ls.generate_state(1)[0])

            logger.debug(
                "{} - Trial {:04d} seeds: rates={}, longevity={}",
                job_id,
                tid,
                rates_seed,
                longevity_seed,
            )

        trial_args.append((job_id, tid, rates_seed, longevity_seed, case_file, overrides, run_dir))

    n_trials = len(trial_args)

    logger.debug("{} - Launching {} trials (n_jobs={})", job_id, n_trials, n_jobs)

    # -------------------------------------------------------------
    # Run trials (parallel if needed)
    # -------------------------------------------------------------
    results = []
    completed = 0

    HEARTBEAT_SEC = 1
    last_update = time.monotonic()

    def _on_trial_done(result):
        results.append(result)

    if n_trials == 1:
        results = [run_trial(*trial_args[0])]
    else:
        with Pool(processes=n_jobs) as pool:
            async_results = [
                pool.apply_async(run_trial, args, callback=_on_trial_done) for args in trial_args
            ]

            with tqdm(
                total=n_trials,
                desc=f"{job_id}",
                unit="trial",
                dynamic_ncols=True,
                bar_format="{desc}: {percentage:.1f}% |{bar}| {postfix}",
            ) as pbar:
                while completed < n_trials:
                    newly_completed = len(results) - completed

                    if newly_completed:
                        completed += newly_completed
                        pbar.update(newly_completed)

                    now = time.monotonic()
                    if now - last_update >= HEARTBEAT_SEC:
                        elapsed = pbar.format_dict["elapsed"] or 0.0
                        spt = elapsed / max(completed, 1)

                        pbar.set_postfix_str(
                            f"elapsed={elapsed:.1f}s, "
                            f"running={completed}/{n_trials}, "
                            f"s_per_trial={spt:.1f}s"
                        )
                        pbar.refresh()
                        last_update = now

                    time.sleep(0.2)

            # propagate worker exceptions
            for r in async_results:
                r.get()

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    solved = [r for r in results if r["status"] == "solved"]
    failed = [r for r in results if r["status"] != "solved"]

    logger.info(
        "{} - Trials complete: {} solved, {} failed",
        job_id,
        len(solved),
        len(failed),
    )

    if failed:
        logger.warning(
            "{} - Failed trial IDs: {}",
            job_id,
            [r["trial_id"] for r in failed],
        )


if __name__ == "__main__":
    main()
