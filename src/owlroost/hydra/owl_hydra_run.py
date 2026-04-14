# src/owlroost/hydra/owl_hydra_run.py

import multiprocessing as mp
from pathlib import Path

import hydra
import numpy as np
from hydra.core.hydra_config import HydraConfig
from loguru import logger
from omegaconf import DictConfig

from owlroost.cli.utils import normalize_case_file_overrides
from owlroost.core.configure_logging import configure_logging
from owlroost.core.override_parser import hydra_overrides_to_dict
from owlroost.core.progress import (
    init_progress,
    record_progress,
)
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
    try:
        return int(overrides.get("trial", {}).get(key, default))
    except Exception:
        return default


def spawn_trial_seeds(master_seed: int, trial_ids: list[int]) -> dict[int, tuple[int, int]]:
    """
    Deterministically generate (rates_seed, longevity_seed) per trial.
    Pure function. No Hydra dependency.
    """
    seed_map = {}

    for tid in trial_ids:
        trial_ss = np.random.SeedSequence(master_seed, spawn_key=(tid,))
        rs, ls = trial_ss.spawn(2)

        rates_seed = int(rs.generate_state(1)[0])
        longevity_seed = int(ls.generate_state(1)[0])

        seed_map[tid] = (rates_seed, longevity_seed)

    return seed_map


def _safe_run_trial(payload):
    """
    payload = (worker_fn, args)
    """
    worker_fn, args = payload

    (
        job_id,
        tid,
        rates_seed,
        longevity_seed,
        case_file,
        overrides,
        run_dir,
        master_seed,
        longevity_cfg,
    ) = args

    try:
        return worker_fn(*args)

    except Exception as e:
        logger.exception(
            "{} - Trial {:04d} crashed: {}",
            job_id,
            tid,
            e,
        )

        return {
            "trial_id": tid,
            "rates_seed": rates_seed,
            "longevity_seed": longevity_seed,
            "status": "error",
            "output": None,
            "error": str(e),
        }


# ---------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------
def orchestrate_trials(
    *,
    job_id: str,
    master_seed: int,
    trial_ids: list[int],
    use_trial_seeds: bool,
    n_jobs: int,
    case_file: Path,
    overrides: dict,
    run_dir: Path,
    longevity_cfg: dict,
    progress_file: Path | None = None,
    worker_fn=None,
):
    """
    Pure orchestration layer.
    Robust against worker crashes.
    Fully testable.
    """

    if worker_fn is None:
        worker_fn = run_trial

    if use_trial_seeds:
        seed_map = spawn_trial_seeds(master_seed, trial_ids)
    else:
        seed_map = {tid: (None, None) for tid in trial_ids}

    trial_args = []
    for tid in trial_ids:
        rates_seed, longevity_seed = seed_map[tid]

        logger.debug(
            "{} - Trial {:04d} seeds: rates={}, longevity={}",
            job_id,
            tid,
            rates_seed,
            longevity_seed,
        )

        trial_args.append(
            (
                job_id,
                tid,
                rates_seed,
                longevity_seed,
                case_file,
                overrides,
                run_dir,
                master_seed,
                longevity_cfg,
            )
        )

    is_single_trial = len(trial_ids) == 1
    results = []

    # -----------------------------------------------------
    # Single-process mode
    # -----------------------------------------------------
    if n_jobs == 1:
        for args in trial_args:
            r = _safe_run_trial((worker_fn, args))
            results.append(r)

            tid = r.get("trial_id")
            if progress_file is not None and tid is not None:
                status = r.get("status", "unknown")
                record_progress(progress_file, job_id, tid, status)

    # -----------------------------------------------------
    # Multiprocessing mode
    # -----------------------------------------------------
    else:
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=n_jobs) as pool:
            payloads = [(worker_fn, args) for args in trial_args]
            for r in pool.imap_unordered(_safe_run_trial, payloads):
                results.append(r)
                tid = r.get("trial_id")
                if progress_file is not None and tid is not None:
                    status = r.get("status", "unknown")
                    record_progress(progress_file, job_id, tid, status)

    solved = [r for r in results if r["status"] == "solved"]
    failed = [r for r in results if r["status"] != "solved"]

    logger.debug(
        "{} - Trials complete: {} solved, {} failed",
        job_id,
        len(solved),
        len(failed),
    )

    if failed:
        logger.debug(
            "{} - Failed trial IDs: {}",
            job_id,
            [r["trial_id"] for r in sorted(failed, key=lambda x: x["trial_id"])],
        )

        if is_single_trial:
            err = failed[0].get("error")
            if err:
                logger.error("\n--- Trial Failure Detail ---\n{}\n", err)

    if results is not None:
        results.sort(key=lambda r: r["trial_id"])
    return results


# ---------------------------------------------------------------------
# Master seed
# ---------------------------------------------------------------------
def get_master_seed(cfg: DictConfig, job_id: str) -> int | None:
    case_roost = getattr(cfg.case, "ROOST", None)

    if case_roost and getattr(case_roost, "master_seed", None) is not None:
        master_seed = int(case_roost.master_seed)
        source = "case"

    elif getattr(cfg.roost, "master_seed", None) is not None:
        master_seed = int(cfg.roost.master_seed)
        source = "hydra"

    else:
        # No seed defined → deterministic mode
        logger.debug("{} - No master_seed defined (deterministic mode)", job_id)
        return None

    if not fits_uint32(master_seed):
        raise ValueError(f"Invalid master_seed (must fit uint32): {master_seed}")

    logger.debug("{} - Using master_seed={} (source={})", job_id, master_seed, source)
    return master_seed


# ---------------------------------------------------------------------
# HYDRA ENTRYPOINT
# ---------------------------------------------------------------------
@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg):
    run_hydra_job(cfg)


def run_hydra_job(cfg: DictConfig):
    if not hasattr(cfg, "case") or not hasattr(cfg.case, "file"):
        raise RuntimeError("Hydra config must define case.file")

    case_file = resolve_case_file(cfg.case.file)

    configure_logging(cfg)

    try:
        hc = HydraConfig.get()
        raw_overrides = hc.overrides.task
        job_id = get_job_id(hc)
        mode = hc.mode
    except ValueError:
        raw_overrides = []
        job_id = "test-job"
        mode = "UNIT_TEST"

    overrides = hydra_overrides_to_dict(raw_overrides)
    clean_overrides = normalize_case_file_overrides(raw_overrides)

    logger.debug("{} - overrides: {}", job_id, " ".join(clean_overrides))

    run_dir = get_run_dir()
    logger.debug("{} - Run directory: {}", job_id, run_dir.relative_to(PROJECT_ROOT))

    progress_file = run_dir.parent / "progress.log"
    init_progress(progress_file)

    master_seed = get_master_seed(cfg, job_id)

    save_hydra_metadata(
        run_dir=run_dir,
        mode=mode,
        job_id=job_id,
        overrides=raw_overrides,
        extra={"master_seed": master_seed},
    )

    trial_cfg = cfg.trial
    n_jobs = int(trial_cfg.n_jobs)

    trial_id_override = _extract_trial_override(overrides, "id")
    trial_count_override = _extract_trial_override(overrides, "count", default=int(trial_cfg.count))

    use_trial_seeds = trial_id_override is not None or trial_count_override > 1

    if trial_id_override is not None:
        trial_ids = [trial_id_override]
    elif trial_count_override == 1:
        trial_ids = [0]
    else:
        trial_ids = list(range(trial_count_override))

    orchestrate_trials(
        job_id=job_id,
        master_seed=master_seed,
        trial_ids=trial_ids,
        use_trial_seeds=use_trial_seeds,
        n_jobs=n_jobs,
        case_file=case_file,
        overrides=overrides,
        run_dir=run_dir,
        longevity_cfg=dict(cfg.longevity),
        progress_file=progress_file,
    )


if __name__ == "__main__":
    main()
