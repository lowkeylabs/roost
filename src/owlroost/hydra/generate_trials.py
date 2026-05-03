from __future__ import annotations

import shutil
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path

import hydra
import numpy as np
import toml
import yaml
from hydra.core.hydra_config import HydraConfig
from loguru import logger
from omegaconf import DictConfig
from owlplanner.config.plan_bridge import config_to_plan, plan_to_config

# OWL imports (the key upgrade)
from owlplanner.config.toml_io import load_toml

from ..schema.runtime_defaults import build_runtime_defaults

# =========================================================
# Helpers
# =========================================================


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
    """
    Apply Hydra override strings (dot notation) onto dict.
    """
    out = deepcopy(base)

    for o in overrides:
        if "=" not in o:
            continue

        key, value = o.split("=", 1)

        # basic parsing
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


# =========================================================
# Main generator
# =========================================================


def generate_trials(cfg: DictConfig):
    case_file = resolve_case_file(cfg.case.file)
    run_path = get_run_dir()
    run_path.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------
    # 1. Load case
    # ----------------------------------------
    diconf, dirname, _ = load_toml(str(case_file))

    # ----------------------------------------
    # 2. Merge with OWL defaults (CRITICAL)
    # ----------------------------------------
    defaults = build_runtime_defaults()

    def deep_merge(base, override):
        for k, v in override.items():
            if k not in base:
                base[k] = v
            elif isinstance(base[k], dict) and isinstance(v, dict):
                deep_merge(base[k], v)
            else:
                base[k] = v
        return base

    diconf = deep_merge(defaults, diconf)

    # ----------------------------------------
    # 3. Minimal normalization (ONLY what OWL won't fix)
    # ----------------------------------------
    bi = diconf.setdefault("basic_info", {})

    names = bi.get("names")
    le = bi.get("life_expectancy")

    if not names and not le:
        bi["names"] = ["A"]
        bi["life_expectancy"] = [90]

    elif le and not names:
        n = len(le)
        bi["names"] = [f"P{i+1}" for i in range(n)]

    elif names and not le:
        bi["life_expectancy"] = [90] * len(names)

    elif len(names) != len(le):
        n = min(len(names), len(le))
        bi["names"] = names[:n]
        bi["life_expectancy"] = le[:n]

    bi.setdefault("status", "married")

    this_year = date.today().year

    names = bi["names"]
    le = bi.get("life_expectancy", [])

    # Ensure life_expectancy exists and is valid length
    if not le:
        le = [90] * len(names)
    elif len(le) != len(names):
        le = le[: len(names)] + [le[-1]] * (len(names) - len(le))

    bi["life_expectancy"] = le

    # Adjust DOB to ensure positive horizon
    fixed_dob = []

    for i in range(len(names)):
        expectancy = le[i]

        # target current age comfortably below expectancy
        target_age = min(50, expectancy - 10)
        target_age = max(30, target_age)  # avoid unrealistic young ages

        dob_year = this_year - target_age
        fixed_dob.append(f"{dob_year}-01-01")

    bi["date_of_birth"] = fixed_dob

    # ----------------------------------------
    # Ensure case_name
    # ----------------------------------------
    diconf.setdefault("case_name", case_file.stem)

    # ----------------------------------------
    # 4. Normalize case via OWL
    # ----------------------------------------
    case_plan = config_to_plan(diconf, dirname=dirname, loadHFP=False)
    case_dict = plan_to_config(case_plan)

    case_root = run_path.parents[2]  # results/case
    case_norm = case_root / "case.normalized.toml"

    case_norm.parent.mkdir(parents=True, exist_ok=True)

    if not case_norm.exists():
        case_norm.write_text(toml.dumps(case_dict))

    # ----------------------------------------
    # 5. Apply Hydra overrides
    # ----------------------------------------
    hydra_cfg = HydraConfig.get()

    overrides_list = []
    if hasattr(hydra_cfg, "overrides") and hasattr(hydra_cfg.overrides, "task"):
        overrides_list = hydra_cfg.overrides.task or []

    diconf_run = apply_override_list(diconf, overrides_list)
    diconf_run.setdefault("case_name", diconf["case_name"])

    # ----------------------------------------
    # 6. Normalize run via OWL
    # ----------------------------------------
    run_plan = config_to_plan(diconf_run, dirname=dirname, loadHFP=False)
    run_dict = plan_to_config(run_plan)

    run_norm_path = run_path / "run.normalized.toml"
    run_norm_path.write_text(toml.dumps(run_dict))

    # ----------------------------------------
    # 7. Trials setup
    # ----------------------------------------
    roost_cfg = getattr(cfg, "roost", None)

    master_seed = getattr(roost_cfg, "master_seed", None) or 0
    trial_count = int(getattr(roost_cfg, "trials_per_run", 1))

    trial_ids = list(range(trial_count))
    seed_map = spawn_trial_seeds(master_seed, trial_ids)

    trial_root = run_path / "trials"
    trial_root.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------
    # 8. Copy HFP once per run
    # ----------------------------------------
    hfp_file = run_dict.get("household_financial_profile", {}).get("HFP_file_name")

    hfp_dst_name = None
    if hfp_file and str(hfp_file) not in ("", "None"):
        src = case_file.parent / hfp_file
        if src.exists():
            dst = run_path / src.name
            if src.resolve() != dst.resolve():
                shutil.copy2(src, dst)
            hfp_dst_name = src.name

    # ----------------------------------------
    # 9. Generate trials
    # ----------------------------------------
    for tid in trial_ids:
        tdir = trial_root / f"{tid:04d}"
        tdir.mkdir(parents=True, exist_ok=True)

        rates_seed, longevity_seed = seed_map.get(tid, (None, None))

        trial_dict = deepcopy(run_dict)

        # Inject seeds (only if multi-trial)
        if trial_count > 1:
            if rates_seed is not None:
                rs = trial_dict.setdefault("rates_selection", {})
                rs["rates_seed"] = rates_seed
                if trial_dict.get("rates_selection", {}).get("method") in (
                    "bootstrap_sor",
                    "bootstrap",
                ):
                    rs["reproducible_rates"] = True

            if longevity_seed is not None:
                trial_dict.setdefault("longevity", {})["seed"] = longevity_seed

        # Inject roost metadata
        trial_dict.setdefault("roost", {}).update(
            {
                "trial_id": tid,
                "run_name": run_path.name,
                "master_seed": master_seed,
                "rates_seed": rates_seed,
                "longevity_seed": longevity_seed,
            }
        )

        # Fix HFP path
        if hfp_dst_name:
            rel_path = Path("../../") / hfp_dst_name
            trial_dict.setdefault("household_financial_profile", {})["HFP_file_name"] = str(
                rel_path
            )

        # Final normalization
        trial_plan = config_to_plan(trial_dict, dirname=str(tdir), loadHFP=False)
        trial_dict = plan_to_config(trial_plan)

        # Write trial
        (tdir / "trial.normalized.toml").write_text(toml.dumps(trial_dict))

        meta = {
            "trial_id": tid,
            "rates_seed": rates_seed,
            "longevity_seed": longevity_seed,
            "created_at": datetime.now().isoformat(),
        }

        (tdir / "trial_meta.yaml").write_text(yaml.dump(meta))

    logger.debug(f"Generated {len(trial_ids)} trials at {run_path}")


# =========================================================
# Hydra entrypoint
# =========================================================


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: DictConfig):
    generate_trials(cfg)


if __name__ == "__main__":
    main()
