from __future__ import annotations

import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import hydra
import numpy as np
import toml
import yaml
from hydra.core.hydra_config import HydraConfig
from loguru import logger
from omegaconf import DictConfig, OmegaConf


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def resolve_case_file(case_file: str | Path) -> Path:
    p = Path(case_file)
    if not p.exists():
        raise FileNotFoundError(f"Case file not found: {p}")
    return p.resolve()


def get_run_dir() -> Path:
    hc = HydraConfig.get()
    return Path(hc.runtime.output_dir).resolve()


def spawn_trial_seeds(master_seed: int, trial_ids: list[int]):
    rng = np.random.default_rng(master_seed)
    seeds = rng.integers(0, 2**32 - 1, size=(len(trial_ids), 2))
    return {tid: (int(s[0]), int(s[1])) for tid, s in zip(trial_ids, seeds, strict=False)}


def apply_override_list(base: dict, overrides: list[str]) -> dict:
    out = deepcopy(base)

    for o in overrides:
        if "=" not in o:
            continue

        key, value = o.split("=", 1)

        try:
            import tomllib

            value = tomllib.loads(value)
        except Exception:
            value = value.strip('"')

        parts = key.split(".")
        d = out
        for p in parts[:-1]:
            d = d.setdefault(p, {})

        d[parts[-1]] = value

    return out


def filter_case_overrides(overrides: list[str]) -> list[str]:
    keep = []
    for o in overrides:
        if o.startswith(("hydra.", "runtime.", "trial.")):
            continue
        keep.append(o)
    return keep


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def generate_trials(cfg: DictConfig):
    case_file = resolve_case_file(cfg.case.file)

    # Hydra-managed directories
    run_path = get_run_dir()
    exp_path = run_path.parent

    run_path.mkdir(parents=True, exist_ok=True)
    exp_path.mkdir(parents=True, exist_ok=True)

    # results/<case>/<date>/<time>
    experiment_id = f"{exp_path.parent.name}/{exp_path.name}"

    # ----------------------------------------
    # Hydra context
    # ----------------------------------------
    try:
        hc = HydraConfig.get()
        run_idx = int(hc.job.num)
        raw_overrides = getattr(hc.overrides, "task", []) or []
    except Exception:
        run_idx = 0
        raw_overrides = []

    case_overrides = filter_case_overrides(raw_overrides)

    # ----------------------------------------
    # Save experiment-level case.toml (once)
    # ----------------------------------------
    exp_case_path = exp_path / "case.toml"
    if not exp_case_path.exists():
        shutil.copy2(case_file, exp_case_path)

    # ----------------------------------------
    # Load base TOML
    # ----------------------------------------
    case_dict = toml.load(case_file)

    # ----------------------------------------
    # Apply overrides → run_dict
    # ----------------------------------------
    run_dict = apply_override_list(case_dict, case_overrides)

    # ----------------------------------------
    # Runtime / roost config
    # ----------------------------------------

    cfg_dict = OmegaConf.to_container(cfg, resolve=True)

    roost_cfg = cfg_dict.get("roost", {})

    master_seed = int(roost_cfg.get("master_seed", 0) or 0)

    trial_count = roost_cfg.get("trials_per_run")
    if trial_count is None:
        trial_count = 1
    trial_count = int(trial_count)

    run_dict.setdefault("roost", {})
    run_dict["roost"].update(
        {
            "run_id": run_idx,
            "experiment_id": experiment_id,
            "master_seed": master_seed,
            "trials_per_run": trial_count,
        }
    )

    # ----------------------------------------
    # Copy HFP to run folder
    # ----------------------------------------
    hfp_file = case_dict.get("household_financial_profile", {}).get("HFP_file_name")

    hfp_dst_name = None
    if hfp_file:
        src = (case_file.parent / hfp_file).resolve()
        if not src.exists():
            raise FileNotFoundError(f"HFP file not found: {src}")

        dst = run_path / src.name
        if not dst.exists():
            shutil.copy2(src, dst)

        hfp_dst_name = src.name

        run_dict.setdefault("household_financial_profile", {})["HFP_file_name"] = hfp_dst_name

    # ----------------------------------------
    # Save run.toml
    # ----------------------------------------
    (run_path / "run.toml").write_text(toml.dumps(run_dict))

    # ----------------------------------------
    # Trial setup
    # ----------------------------------------
    trial_ids = list(range(trial_count))
    seed_map = spawn_trial_seeds(master_seed, trial_ids)

    trial_root = run_path / "trials"
    trial_root.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------
    # Generate trials
    # ----------------------------------------
    for tid in trial_ids:
        tdir = trial_root / f"{tid:04d}"
        tdir.mkdir(parents=True, exist_ok=True)

        trial_dict = deepcopy(run_dict)

        rates_seed, longevity_seed = seed_map[tid]

        if trial_count > 1:
            trial_dict.setdefault("rates_selection", {})["rates_seed"] = rates_seed
            trial_dict.setdefault("longevity", {})["seed"] = longevity_seed

        trial_dict.setdefault("roost", {}).update(
            {
                "trial_id": tid,
                "run_id": run_idx,
                "experiment_id": experiment_id,
                "rates_seed": rates_seed,
                "longevity_seed": longevity_seed,
            }
        )

        if hfp_dst_name:
            trial_dict.setdefault("household_financial_profile", {})["HFP_file_name"] = str(
                Path("../../") / hfp_dst_name
            )

        (tdir / "trial.toml").write_text(toml.dumps(trial_dict))

        meta = {
            "trial_id": tid,
            "run_id": run_idx,
            "rates_seed": rates_seed,
            "longevity_seed": longevity_seed,
            "created_at": datetime.now().isoformat(),
        }

        (tdir / "trial_meta.yaml").write_text(yaml.dump(meta))

    logger.debug(f"Generated run_{run_idx} with {trial_count} trials at {exp_path}")


# ---------------------------------------------------------
# Hydra entrypoint
# ---------------------------------------------------------
@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: DictConfig):
    generate_trials(cfg)


if __name__ == "__main__":
    main()
