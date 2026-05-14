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

from owlroost.schema.system_models import (
    RoostRuntimeConfig,
    RuntimeEnvironmentConfig,
)


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

    cfg_dict = OmegaConf.to_container(
        cfg,
        resolve=True,
    )

    SECTION_MODELS = {
        "roost_runtime": RoostRuntimeConfig,
        "runtime_environment": RuntimeEnvironmentConfig,
    }

    section_models = {}

    for section_name, model_cls in SECTION_MODELS.items():
        model = model_cls(
            **cfg_dict.get(
                section_name,
                {},
            )
        )

        section_models[section_name] = model

        section_dict = model.model_dump(
            exclude_none=True,
        )

        if section_dict:
            run_dict[section_name] = section_dict

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
    # Save Hydra provenance / effective config
    # ----------------------------------------

    resolved_cfg = OmegaConf.to_container(
        cfg,
        resolve=True,
    )

    # Full resolved Hydra config
    effective_cfg_path = run_path / "effective_config.yaml"

    with open(effective_cfg_path, "w") as f:
        yaml.safe_dump(
            resolved_cfg,
            f,
            sort_keys=False,
        )

    # Compact override provenance
    hc = HydraConfig.get()

    overrides_payload = {
        "task_overrides": list(getattr(hc.overrides, "task", []) or []),
        "hydra_overrides": list(getattr(hc.overrides, "hydra", []) or []),
        "runtime": {
            "job_num": hc.job.num,
            "output_dir": hc.runtime.output_dir,
            "cwd": hc.runtime.cwd,
            "choices": dict(hc.runtime.choices),
        },
    }

    overrides_path = run_path / "hydra_overrides.yaml"

    with open(overrides_path, "w") as f:
        yaml.safe_dump(
            overrides_payload,
            f,
            sort_keys=False,
        )

    # ----------------------------------------
    # Trial setup
    # ----------------------------------------

    roost_runtime = section_models["roost_runtime"]
    trials_per_run = roost_runtime.trials_per_run
    master_seed = roost_runtime.master_seed or 0

    trial_ids = list(range(trials_per_run))
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

        # build longevity and other trial-specific stuff here!

        rate_seed, longevity_seed = seed_map[tid]

        if trials_per_run > 1:
            trial_dict.setdefault("rates_selection", {})["rate_seed"] = rate_seed
            trial_dict.setdefault("rates_selection", {})["reproducible_rates"] = True
            trial_dict.setdefault("longevity", {})["seed"] = longevity_seed

        trial_dict.setdefault("trial_runtime", {}).update(
            {
                "trial_id": tid,
                "run_id": run_idx,
                "experiment_id": experiment_id,
                "rate_seed": rate_seed,
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
            "rate_seed": rate_seed,
            "longevity_seed": longevity_seed,
            "created_at": datetime.now().isoformat(),
        }

        (tdir / "trial_meta.yaml").write_text(yaml.dump(meta))

    logger.debug(f"Generated run_{run_idx} with {trials_per_run} trials at {exp_path}")


# ---------------------------------------------------------
# Hydra entrypoint
# ---------------------------------------------------------
@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: DictConfig):
    generate_trials(cfg)


if __name__ == "__main__":
    main()
