import pytest
from omegaconf import OmegaConf

from owlroost.hydra.generate_trials import generate_trials


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

[household_financial_profile]
HFP_file_name = "hfp.csv"
"""
    )

    # create fake HFP file
    (tmp_path / "hfp.csv").write_text("dummy")

    return case


@pytest.fixture
def hydra_cfg(tmp_case, tmp_path, monkeypatch):
    """
    Build a fake Hydra cfg + mock HydraConfig runtime.
    """

    cfg = OmegaConf.create(
        {
            "case": {"file": str(tmp_case)},
            "roost": {"master_seed": 123, "trials_per_run": 3},
        }
    )

    # ----------------------------------------
    # Mock Hydra runtime
    # ----------------------------------------
    class FakeRuntime:
        output_dir = str(tmp_path / "results/case/2026-01-01/00-00-00/run_0")

    class FakeHydraConfig:
        runtime = FakeRuntime()

        @staticmethod
        def get():
            return FakeHydraConfig()

    monkeypatch.setattr(
        "owlroost.hydra.generate_trials.HydraConfig",
        FakeHydraConfig,
    )

    return cfg


def test_generate_trials_creates_structure(hydra_cfg, tmp_path):
    generate_trials(hydra_cfg)

    root = tmp_path / "results/case/2026-01-01/00-00-00/run_0"

    assert root.exists()

    trials = root / "trials"
    assert trials.exists()

    # 3 trials created
    trial_dirs = sorted(trials.glob("*"))
    assert len(trial_dirs) == 3

    # check each trial
    for tdir in trial_dirs:
        assert (tdir / "trial.normalized.toml").exists()
        assert (tdir / "trial_meta.yaml").exists()


def test_trial_toml_contains_seeds(hydra_cfg, tmp_path):
    generate_trials(hydra_cfg)

    root = tmp_path / "results/case/2026-01-01/00-00-00/run_0"
    trial0 = root / "trials/0000"

    content = (trial0 / "trial.normalized.toml").read_text()

    assert "rates_seed" in content
    assert "longevity_seed" in content


def test_hfp_copied_once(hydra_cfg, tmp_path):
    generate_trials(hydra_cfg)

    run_dir = tmp_path / "results/case/2026-01-01/00-00-00/run_0"

    # should exist in run dir
    assert (run_dir / "hfp.csv").exists()


def test_case_normalized_written(hydra_cfg, tmp_path):
    generate_trials(hydra_cfg)

    case_root = tmp_path / "results/case"
    assert (case_root / "case.normalized.toml").exists()
