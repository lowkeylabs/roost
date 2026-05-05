import pytest
import toml
import yaml
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

    # fake HFP file
    (tmp_path / "hfp.csv").write_text("dummy")

    return case


@pytest.fixture
def hydra_cfg(tmp_case, tmp_path, monkeypatch):
    cfg = OmegaConf.create(
        {
            "case": {"file": str(tmp_case)},
            "roost": {"master_seed": 123, "trials_per_run": 3},
        }
    )

    class FakeRuntime:
        output_dir = str(tmp_path / "results/case/2026-01-01/00-00-00/run_0")

    class FakeHydraConfig:
        runtime = FakeRuntime()

        class job:
            num = 0

        class overrides:
            task = []

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

    # run-level file
    assert (root / "run.toml").exists()

    trials = root / "trials"
    assert trials.exists()

    trial_dirs = sorted(trials.glob("*"))
    assert len(trial_dirs) == 3

    for tdir in trial_dirs:
        assert (tdir / "trial.toml").exists()
        assert (tdir / "trial_meta.yaml").exists()


def test_trial_toml_contains_seeds(hydra_cfg, tmp_path):
    generate_trials(hydra_cfg)

    trial0 = tmp_path / "results/case/2026-01-01/00-00-00/run_0/trials/0000/trial.toml"

    data = toml.load(trial0)

    # seeds exist in both locations
    assert "rates_seed" in data["roost"]
    assert "longevity_seed" in data["roost"]

    assert "rates_seed" in data["rates_selection"]
    assert "seed" in data["longevity"]


def test_hfp_copied_once_and_rewritten(hydra_cfg, tmp_path):
    generate_trials(hydra_cfg)

    run_dir = tmp_path / "results/case/2026-01-01/00-00-00/run_0"

    # copied to run dir
    assert (run_dir / "hfp.csv").exists()

    # rewritten relative path inside trial
    trial0 = run_dir / "trials/0000/trial.toml"
    data = toml.load(trial0)

    assert data["household_financial_profile"]["HFP_file_name"] == "../../hfp.csv"


def test_trial_meta_yaml(hydra_cfg, tmp_path):
    generate_trials(hydra_cfg)

    meta_file = tmp_path / "results/case/2026-01-01/00-00-00/run_0/trials/0000/trial_meta.yaml"

    meta = yaml.safe_load(meta_file.read_text())

    assert meta["trial_id"] == 0
    assert meta["run_id"] == 0
    assert "rates_seed" in meta
    assert "longevity_seed" in meta
    assert "created_at" in meta


def test_experiment_case_written_once(hydra_cfg, tmp_path):
    generate_trials(hydra_cfg)

    exp_dir = tmp_path / "results/case/2026-01-01/00-00-00"
    assert (exp_dir / "case.toml").exists()
