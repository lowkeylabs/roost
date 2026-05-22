from copy import deepcopy

import pytest
import toml
import yaml
from loguru import logger
from omegaconf import OmegaConf

from owlroost.hydra.generate_trials import (
    generate_trials,
    materialize_execution_plan,
)

# =========================================================
# Fixtures
# =========================================================


@pytest.fixture
def tmp_case(tmp_path):
    case = tmp_path / "case.toml"

    case.write_text(
        """
[basic_info]
life_expectancy = [65, 67]

[longevity]
apply_to_plan = true

[rates_selection]
rate_seed=987_654_321

[household_financial_profile]
HFP_file_name = "hfp.csv"
"""
    )

    # -----------------------------------------------------
    # Fake HFP file
    # -----------------------------------------------------

    (tmp_path / "hfp.csv").write_text("dummy")

    return case


@pytest.fixture
def hydra_cfg(
    tmp_case,
    tmp_path,
    monkeypatch,
):
    cfg = OmegaConf.create(
        {
            "case": {
                "file": str(tmp_case),
            },
            "roost_runtime": {
                "master_seed": 123,
                "trials_per_run": 3,
                "workers_per_run": 4,
            },
        }
    )

    # =====================================================
    # Fake Hydra Runtime
    # =====================================================

    class FakeRuntime:
        output_dir = str(tmp_path / "results/case/2026-01-01/00-00-00/run_0")

        cwd = str(tmp_path)

        choices = {}

    # =====================================================
    # Fake Hydra Config
    # =====================================================

    class FakeHydraConfig:
        runtime = FakeRuntime()

        class job:
            num = 0

        class overrides:
            task = []
            hydra = []

        @staticmethod
        def get():
            return FakeHydraConfig()

    monkeypatch.setattr(
        "owlroost.hydra.generate_trials.HydraConfig",
        FakeHydraConfig,
    )

    return cfg


# =========================================================
# Structure
# =========================================================


def test_generate_trials_creates_structure(
    hydra_cfg,
    tmp_path,
):
    generate_trials(hydra_cfg)

    root = tmp_path / "results/case/2026-01-01/00-00-00/run_0"

    assert root.exists()

    # -----------------------------------------------------
    # Run-level files
    # -----------------------------------------------------

    assert (root / "run.toml").exists()

    assert (root / "effective_config.yaml").exists()

    assert (root / "hydra_overrides.yaml").exists()

    # -----------------------------------------------------
    # Trials
    # -----------------------------------------------------

    trials = root / "trials"

    assert trials.exists()

    trial_dirs = sorted(trials.glob("*"))

    assert len(trial_dirs) == 3

    for tdir in trial_dirs:
        assert (tdir / "trial.toml").exists()

        assert (tdir / "trial_meta.yaml").exists()


# =========================================================
# Seeds
# =========================================================


def test_trial_toml_contains_seeds(
    hydra_cfg,
    tmp_path,
):
    generate_trials(hydra_cfg)

    trial0 = tmp_path / "results/case/2026-01-01/00-00-00/run_0/trials/0000/trial.toml"

    data = toml.load(trial0)

    logger.debug(data)

    assert "rate_seed" in data["trial_runtime"]

    assert "longevity_seed" in data["trial_runtime"]


# =========================================================
# HFP Handling
# =========================================================


def test_hfp_copied_once_and_rewritten(
    hydra_cfg,
    tmp_path,
):
    generate_trials(hydra_cfg)

    run_dir = tmp_path / "results/case/2026-01-01/00-00-00/run_0"

    # -----------------------------------------------------
    # Copied once to run dir
    # -----------------------------------------------------

    assert (run_dir / "hfp.csv").exists()

    # -----------------------------------------------------
    # Relative rewrite inside trial
    # -----------------------------------------------------

    trial0 = run_dir / "trials/0000/trial.toml"

    data = toml.load(trial0)

    assert data["household_financial_profile"]["HFP_file_name"] == "../../hfp.csv"


# =========================================================
# Trial Meta
# =========================================================


def test_trial_meta_yaml(
    hydra_cfg,
    tmp_path,
):
    generate_trials(hydra_cfg)

    meta_file = tmp_path / "results/case/2026-01-01/00-00-00/run_0/trials/0000/trial_meta.yaml"

    meta = yaml.safe_load(meta_file.read_text())

    assert meta["trial_id"] == 0

    assert meta["run_id"] == 0

    assert "rate_seed" in meta

    assert "longevity_seed" in meta

    assert "created_at" in meta


# =========================================================
# Experiment Case
# =========================================================


def test_experiment_case_written_once(
    hydra_cfg,
    tmp_path,
):
    generate_trials(hydra_cfg)

    exp_dir = tmp_path / "results/case/2026-01-01/00-00-00"

    assert (exp_dir / "session.toml").exists()


# =========================================================
# Hydra Provenance
# =========================================================


def test_hydra_overrides_written(
    hydra_cfg,
    tmp_path,
):
    generate_trials(hydra_cfg)

    path = tmp_path / "results/case/2026-01-01/00-00-00/run_0/hydra_overrides.yaml"

    assert path.exists()

    data = yaml.safe_load(path.read_text())

    assert "runtime" in data

    assert data["runtime"]["job_num"] == 0

    assert "cwd" in data["runtime"]

    assert "output_dir" in data["runtime"]


# =========================================================
# Effective Config
# =========================================================


def test_effective_config_written(
    hydra_cfg,
    tmp_path,
):
    generate_trials(hydra_cfg)

    path = tmp_path / "results/case/2026-01-01/00-00-00/run_0/effective_config.yaml"

    assert path.exists()

    data = yaml.safe_load(path.read_text())

    assert "case" in data

    assert "roost_runtime" in data


# =========================================================
# Execution Plan Materialization
# =========================================================


def test_explicit_solver_is_preserved():
    run_dict = {
        "solver_options": {
            "solver": "HiGHS",
        },
        "roost_runtime": {
            "workers_per_run_mode": "auto",
            "auto_workers_by_solver": {
                "HiGHS": 14,
            },
        },
    }

    out = materialize_execution_plan(deepcopy(run_dict))

    assert out["solver_options"]["solver"] == "HiGHS"

    assert out["roost_runtime"]["resolved_solver"] == "HiGHS"

    assert out["roost_runtime"]["resolved_workers_per_run"] == 14


def test_default_solver_materialized_when_auto_workers(
    monkeypatch,
):
    monkeypatch.setattr(
        "owlroost.hydra.generate_trials.mosek_available",
        lambda: True,
    )

    run_dict = {
        "solver_options": {
            "solver": "default",
        },
        "roost_runtime": {
            "workers_per_run_mode": "auto",
            "auto_workers_by_solver": {
                "MOSEK": 6,
                "HiGHS": 14,
            },
        },
    }

    out = materialize_execution_plan(deepcopy(run_dict))

    assert out["solver_options"]["solver"] == "MOSEK"

    assert out["roost_runtime"]["resolved_solver"] == "MOSEK"

    assert out["roost_runtime"]["resolved_workers_per_run"] == 6


def test_default_solver_preserved_when_workers_explicit(
    monkeypatch,
):
    monkeypatch.setattr(
        "owlroost.hydra.generate_trials.mosek_available",
        lambda: True,
    )

    run_dict = {
        "solver_options": {
            "solver": "default",
        },
        "roost_runtime": {
            "workers_per_run": 8,
        },
    }

    out = materialize_execution_plan(deepcopy(run_dict))

    assert out["solver_options"]["solver"] == "default"

    assert out["roost_runtime"]["resolved_solver"] == "MOSEK"

    assert out["roost_runtime"]["resolved_workers_per_run"] == 8


def test_default_solver_materializes_to_highs(
    monkeypatch,
):
    monkeypatch.setattr(
        "owlroost.hydra.generate_trials.mosek_available",
        lambda: False,
    )

    run_dict = {
        "solver_options": {
            "solver": "default",
        },
        "roost_runtime": {
            "workers_per_run_mode": "auto",
            "auto_workers_by_solver": {
                "HiGHS": 14,
            },
        },
    }

    out = materialize_execution_plan(deepcopy(run_dict))

    assert out["solver_options"]["solver"] == "HiGHS"

    assert out["roost_runtime"]["resolved_solver"] == "HiGHS"

    assert out["roost_runtime"]["resolved_workers_per_run"] == 14


def test_execution_metadata_always_materialized(
    monkeypatch,
):
    monkeypatch.setattr(
        "owlroost.hydra.generate_trials.mosek_available",
        lambda: False,
    )

    run_dict = {}

    out = materialize_execution_plan(deepcopy(run_dict))

    runtime = out["roost_runtime"]

    assert "resolved_solver" in runtime

    assert "resolved_workers_per_run" in runtime


def test_explicit_workers_override_auto_mapping(
    monkeypatch,
):
    monkeypatch.setattr(
        "owlroost.hydra.generate_trials.mosek_available",
        lambda: True,
    )

    run_dict = {
        "solver_options": {
            "solver": "MOSEK",
        },
        "roost_runtime": {
            "workers_per_run": 3,
            "workers_per_run_mode": "auto",
            "auto_workers_by_solver": {
                "MOSEK": 6,
            },
        },
    }

    out = materialize_execution_plan(deepcopy(run_dict))

    assert out["roost_runtime"]["resolved_workers_per_run"] == 3
