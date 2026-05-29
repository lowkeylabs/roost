from __future__ import annotations

import importlib.util
import os
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

from owlroost.core.progress_renderers import (
    create_renderer,
)
from owlroost.schema.hydra_expanders import (
    expand_hydra_helpers,
)
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


def clean_pydantic_undefined(obj):
    """
    Recursively remove/normalize
    stringified PydanticUndefined values.
    """

    if isinstance(obj, dict):
        out = {}

        for k, v in obj.items():
            if v == "PydanticUndefined":
                continue

            out[k] = clean_pydantic_undefined(v)

        return out

    if isinstance(obj, list):
        return [clean_pydantic_undefined(v) for v in obj]

    return obj


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

    #    logger.debug(f"Solver={solver}")
    if solver == "default":
        return "MOSEK" if mosek_available() else "HiGHS"

    return solver


def resolve_workers_per_run(
    run_cfg,
    solver=None,
    default=1,
):
    """
    Resolve workers_per_run using precedence:

    1. Explicit workers_per_run override
    2. Solver-aware auto tuning
    3. Default
    """

    runtime = run_cfg.get(
        "roost_runtime",
        {},
    )

    if solver is None:
        solver = resolve_solver_name(run_cfg)

    # -----------------------------------------------------
    # Explicit override ALWAYS wins
    # -----------------------------------------------------

    explicit = runtime.get("workers_per_run")

    if explicit is not None:
        return int(explicit)

    # -----------------------------------------------------
    # Auto mode
    # -----------------------------------------------------

    mode = runtime.get(
        "workers_per_run_mode",
        "auto",
    )

    #    logger.debug(f"Mode={mode}")

    if mode == "auto":
        mapping = runtime.get(
            "auto_workers_by_solver",
            {},
        )

        if solver in mapping:
            return int(mapping[solver])

    # -----------------------------------------------------
    # Fallback
    # -----------------------------------------------------

    return int(default)


def materialize_execution_plan(run_dict):
    solver_options = run_dict.setdefault(
        "solver_options",
        {},
    )

    runtime_section = run_dict.setdefault(
        "roost_runtime",
        {},
    )

    original_solver = solver_options.get(
        "solver",
        "default",
    )

    resolved_solver = resolve_solver_name(run_dict)
    resolved_workers = resolve_workers_per_run(run_dict, solver=resolved_solver)

    workers_mode = runtime_section.get(
        "workers_per_run_mode",
    )

    explicit_workers = runtime_section.get("workers_per_run")

    if original_solver == "default" and workers_mode == "auto" and explicit_workers is None:
        if 0:
            logger.warning(
                "Materializing "
                "solver_options.solver "
                f"from 'default' -> '{resolved_solver}' "
                "because workers_per_run_mode='auto'."
            )

        solver_options["solver"] = resolved_solver

    runtime_section["resolved_solver"] = resolved_solver
    runtime_section["resolved_workers_per_run"] = resolved_workers

    return run_dict


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
    session_id = f"{exp_path.parent.name}/{exp_path.name}"

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
    # Save session-level session.toml (once)
    # ----------------------------------------
    exp_case_path = exp_path / "session.toml"
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
    # Expand Hydra helper fields (e.g. rates_selection.from_to)
    # ----------------------------------------

    run_dict = expand_hydra_helpers(
        run_dict,
    )

    # -------------------------
    # Runtime / roost config
    # ----------------------------------------

    cfg_dict = clean_pydantic_undefined(
        OmegaConf.to_container(
            cfg,
            resolve=True,
        )
    )

    cfg_dict = expand_hydra_helpers(cfg_dict)

    SECTION_MODELS = {
        "roost_runtime": RoostRuntimeConfig,
        "runtime_environment": RuntimeEnvironmentConfig,
    }

    section_models = {}

    for section_name, model_cls in SECTION_MODELS.items():
        section_cfg = clean_pydantic_undefined(
            cfg_dict.get(
                section_name,
                {},
            )
        )

        model = model_cls(**section_cfg)

        section_models[section_name] = model

        section_dict = model.model_dump(
            exclude_none=True,
        )

        if section_dict:
            run_dict[section_name] = section_dict

    # ----------------------------------------
    # Copy HFP to run folder
    # ----------------------------------------

    hfp_section = run_dict.setdefault(
        "household_financial_profile",
        {},
    )

    hfp_file = hfp_section.get("HFP_file_name")

    # ----------------------------------------
    # Explicit sentinel: no HFP file
    # ----------------------------------------

    if hfp_file == "None":
        # Preserve literal sentinel
        hfp_section["HFP_file_name"] = "None"

    # ----------------------------------------
    # Real HFP file
    # ----------------------------------------

    elif hfp_file:
        src = (case_file.parent / hfp_file).resolve()

        if not src.exists():
            raise FileNotFoundError(f"HFP file not found: {src}")

        dst = run_path / src.name

        if not dst.exists():
            shutil.copy2(src, dst)

        hfp_section["HFP_file_name"] = src.name

    # ----------------------------------------
    # Auto-materialize execution topology
    # ----------------------------------------

    run_dict = materialize_execution_plan(run_dict)

    runtime_cfg = section_models.get("roost_runtime")
    env_cfg = section_models.get("runtime_environment")

    if runtime_cfg and env_cfg:
        runtime_section = run_dict.get(
            "roost_runtime",
            {},
        )

        resolved_solver = runtime_section.get("resolved_solver")

        workers_mode = runtime_section.get("workers_per_run_mode")

        # -------------------------------------------------
        # Solver-aware auto execution topology
        # -------------------------------------------------

        auto_env = {}

        if workers_mode == "auto":
            auto_env = runtime_section.get(
                "auto_runtime_environment_by_solver",
                {},
            ).get(
                resolved_solver,
                {},
            )

        # -------------------------------------------------
        # Apply defaults ONLY where unset
        # -------------------------------------------------

        for field_name, value in auto_env.items():
            current = getattr(
                env_cfg,
                field_name,
                None,
            )

            # Explicit user override wins
            if current is None:
                setattr(
                    env_cfg,
                    field_name,
                    value,
                )

        # -------------------------------------------------
        # Persist topology provenance
        # -------------------------------------------------

        if auto_env:
            runtime_section["auto_thread_policy"] = {
                "solver": resolved_solver,
                "environment": auto_env,
                "workers_per_run": runtime_section.get("resolved_workers_per_run"),
            }

            # ---------------------------------------------
            # Re-sync updated model back into run_dict
            # ---------------------------------------------

        run_dict["runtime_environment"] = env_cfg.model_dump(
            exclude_none=True,
        )

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

    case_name = run_dict.get("case", {}).get("name")

    if not case_name:
        case_name = case_file.stem

    label_width = int(
        os.environ.get(
            "OWLROOST_PROGRESS_LABEL_WIDTH",
            len(case_name),
        )
    )

    label = f"{case_name}/{run_path.name}"
    desc = f"{label:<{label_width}}: generating {trials_per_run} trials"

    renderer = create_renderer(
        "rich",
        desc=desc,
    )

    renderer.start(trials_per_run)

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
                "session_id": session_id,
                "rate_seed": rate_seed,
                "longevity_seed": longevity_seed,
            }
        )

        hfp_src = "None"
        if hfp_file:
            if hfp_file != "None":
                hfp_src = Path("../../") / hfp_file

        trial_dict.setdefault("household_financial_profile", {})["HFP_file_name"] = str(hfp_src)

        (tdir / "trial.toml").write_text(toml.dumps(trial_dict))

        meta = {
            "trial_id": tid,
            "run_id": run_idx,
            "rate_seed": rate_seed,
            "longevity_seed": longevity_seed,
            "created_at": datetime.now().isoformat(),
        }

        (tdir / "trial_meta.yaml").write_text(yaml.dump(meta))

        renderer.advance(
            1,
            tid + 1,
            trials_per_run,
        )

    renderer.finish()

    # logger.debug(f"Generated run_{run_idx} with {trials_per_run} trials at {exp_path}")


# ---------------------------------------------------------
# Hydra entrypoint
# ---------------------------------------------------------
@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: DictConfig):
    generate_trials(cfg)


if __name__ == "__main__":
    main()
