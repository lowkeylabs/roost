from unittest.mock import patch

from hydra import compose, initialize_config_module
from hydra.core.global_hydra import GlobalHydra

from owlroost.hydra.owl_hydra_run import orchestrate_trials, run_hydra_job


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_seed_spawning_deterministic(mock_run_trial, tmp_path):
    """
    Ensure:
    - Seeds differ per trial
    - Seeds are deterministic across runs
    - Changing master_seed changes results
    """

    captured = []

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, *args):
        captured.append((trial_id, rates_seed, longevity_seed))
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

    case_file = tmp_path / "case.toml"
    case_file.write_text("dummy")

    trial_ids = [0, 1, 2]

    # -----------------------------
    # First run
    # -----------------------------
    orchestrate_trials(
        job_id="job",
        master_seed=12345,
        trial_ids=trial_ids,
        use_trial_seeds=True,
        n_jobs=1,
        case_file=case_file,
        overrides={},
        run_dir=tmp_path,
    )

    first_run = list(captured)
    assert len(first_run) == 3

    # Ensure seeds differ per trial
    assert len(set(first_run)) == 3

    # -----------------------------
    # Second run (same master_seed)
    # -----------------------------
    captured.clear()

    orchestrate_trials(
        job_id="job",
        master_seed=12345,
        trial_ids=trial_ids,
        use_trial_seeds=True,
        n_jobs=1,
        case_file=case_file,
        overrides={},
        run_dir=tmp_path,
    )

    second_run = list(captured)

    # Deterministic across runs
    assert first_run == second_run

    # -----------------------------
    # Third run (different master_seed)
    # -----------------------------
    captured.clear()

    orchestrate_trials(
        job_id="job",
        master_seed=99999,
        trial_ids=trial_ids,
        use_trial_seeds=True,
        n_jobs=1,
        case_file=case_file,
        overrides={},
        run_dir=tmp_path,
    )

    third_run = list(captured)

    # Seeds must change
    assert first_run != third_run


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_seed_independent_of_trial_order(mock_run_trial, tmp_path):
    """
    Ensure:
    - Seed generation depends ONLY on (master_seed, trial_id)
    - Order of trial_ids does NOT affect generated seeds
    """

    case_file = tmp_path / "case.toml"
    case_file.write_text("dummy")

    master_seed = 54321

    # Capture seeds by trial_id
    captured = {}

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, *args):
        captured[trial_id] = (rates_seed, longevity_seed)
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

    # -----------------------------
    # First run: ordered trial_ids
    # -----------------------------
    ordered_ids = [0, 1, 2, 3, 4]

    orchestrate_trials(
        job_id="job",
        master_seed=master_seed,
        trial_ids=ordered_ids,
        use_trial_seeds=True,
        n_jobs=1,
        case_file=case_file,
        overrides={},
        run_dir=tmp_path,
    )

    seeds_ordered = dict(captured)
    assert len(seeds_ordered) == 5

    # Clear capture
    captured.clear()

    # -----------------------------
    # Second run: shuffled order
    # -----------------------------
    shuffled_ids = [3, 0, 4, 1, 2]

    orchestrate_trials(
        job_id="job",
        master_seed=master_seed,
        trial_ids=shuffled_ids,
        use_trial_seeds=True,
        n_jobs=1,
        case_file=case_file,
        overrides={},
        run_dir=tmp_path,
    )

    seeds_shuffled = dict(captured)
    assert len(seeds_shuffled) == 5

    # -----------------------------------
    # Seeds must match per trial_id
    # -----------------------------------
    for tid in ordered_ids:
        assert seeds_ordered[tid] == seeds_shuffled[tid]


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_bootstrap_overrides_injected(mock_run_trial, tmp_path):
    captured = []

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, case_file, overrides, run_dir):
        captured.append((trial_id, rates_seed, overrides))
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[roost]
use_longevity_model = false
""")

    overrides = [
        f"case.file={case_file}",
        "trial.count=2",
        "trial.n_jobs=1",
        "roost.master_seed=11111",
        "roost.use_bootstrap_model=true",
    ]

    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(config_name="config", overrides=overrides)

    run_hydra_job(cfg)

    assert len(captured) == 2

    for _trial_id, rate_seed, overrides in captured:
        assert rate_seed is not None
        assert overrides["rates"]["method"] == "bootstrap_sor"
        assert overrides["rates"]["bootstrap_type"] == "block"
        assert overrides["rates"]["block_size"] == 7
        assert overrides["rates"]["reproducible"] is True


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_overrides_not_shared_between_trials(mock_run_trial, tmp_path):
    seen = []

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, case_file, overrides, run_dir):
        overrides["marker"] = trial_id
        seen.append((trial_id, dict(overrides)))
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

    trial_ids = [0, 1, 2]

    orchestrate_trials(
        job_id="job",
        master_seed=123,
        trial_ids=trial_ids,
        use_trial_seeds=True,
        n_jobs=1,
        case_file=tmp_path / "dummy.toml",
        overrides={},
        run_dir=tmp_path,
    )

    assert seen[0][1]["marker"] == 0
    assert seen[1][1]["marker"] == 1
    assert seen[2][1]["marker"] == 2


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_single_trial_no_stochastic(mock_run_trial, tmp_path):
    captured = []

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, *args):
        captured.append((rates_seed, longevity_seed))
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

    orchestrate_trials(
        job_id="job",
        master_seed=123,
        trial_ids=[0],
        use_trial_seeds=False,
        n_jobs=1,
        case_file=tmp_path / "dummy.toml",
        overrides={},
        run_dir=tmp_path,
    )

    assert captured == [(None, None)]


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_multiple_trials_no_stochastic(mock_run_trial, tmp_path):
    captured = []

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, *args):
        captured.append((trial_id, rates_seed, longevity_seed))
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

    orchestrate_trials(
        job_id="job",
        master_seed=123,
        trial_ids=[0, 1, 2],
        use_trial_seeds=False,
        n_jobs=1,
        case_file=tmp_path / "dummy.toml",
        overrides={},
        run_dir=tmp_path,
    )

    assert len(captured) == 3
    for _, rates_seed, longevity_seed in captured:
        assert rates_seed is None
        assert longevity_seed is None


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_no_bootstrap_does_not_mutate_rates(mock_run_trial, tmp_path):
    captured = []

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, case_file, overrides, run_dir):
        captured.append(overrides)
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

    case_file = tmp_path / "case.toml"
    case_file.write_text("dummy")

    overrides = {"rates": {"method": "historical"}}

    orchestrate_trials(
        job_id="job",
        master_seed=123,
        trial_ids=[0],
        use_trial_seeds=False,
        n_jobs=1,
        case_file=case_file,
        overrides=overrides,
        run_dir=tmp_path,
    )

    assert captured[0]["rates"]["method"] == "historical"


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_combined_bootstrap_and_longevity(mock_run_trial, tmp_path):
    captured = []

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, case_file, overrides, run_dir):
        captured.append((rates_seed, longevity_seed, overrides))
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[roost]
use_longevity_model = false
""")

    overrides = [
        f"case.file={case_file}",
        "trial.count=2",
        "trial.n_jobs=1",
        "roost.master_seed=22222",
        "roost.use_bootstrap_model=true",
        "roost.use_longevity_model=true",
    ]

    # Reset Hydra (important for repeated tests)
    GlobalHydra.instance().clear()

    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(config_name="config", overrides=overrides)

    run_hydra_job(cfg)

    assert len(captured) == 2

    for rates_seed, longevity_seed, overrides in captured:
        assert rates_seed is not None
        assert longevity_seed is not None
        assert overrides["rates"]["method"] == "bootstrap_sor"


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_reproducibility_contract(mock_run_trial, tmp_path):
    """
    Freeze contract:
    Same master_seed + config → identical full result payload.
    Different master_seed → different payload.
    """

    def deterministic_run_trial(job_id, trial_id, rates_seed, longevity_seed, *args):
        # Simulated deterministic output derived from seeds
        return {
            "status": "solved",
            "trial_id": trial_id,
            "rates_seed": rates_seed,
            "longevity_seed": longevity_seed,
            "synthetic_metric": (rates_seed or 0) ^ (longevity_seed or 0),
        }

    mock_run_trial.side_effect = deterministic_run_trial

    trial_ids = [0, 1, 2, 3]

    # --------------------------
    # First run
    # --------------------------
    results_1 = orchestrate_trials(
        job_id="job",
        master_seed=13579,
        trial_ids=trial_ids,
        use_trial_seeds=True,
        n_jobs=1,
        case_file=tmp_path / "dummy.toml",
        overrides={},
        run_dir=tmp_path,
    )

    # --------------------------
    # Second run (same seed)
    # --------------------------
    results_2 = orchestrate_trials(
        job_id="job",
        master_seed=13579,
        trial_ids=trial_ids,
        use_trial_seeds=True,
        n_jobs=1,
        case_file=tmp_path / "dummy.toml",
        overrides={},
        run_dir=tmp_path,
    )

    assert results_1 == results_2

    # --------------------------
    # Third run (different seed)
    # --------------------------
    results_3 = orchestrate_trials(
        job_id="job",
        master_seed=24680,
        trial_ids=trial_ids,
        use_trial_seeds=True,
        n_jobs=1,
        case_file=tmp_path / "dummy.toml",
        overrides={},
        run_dir=tmp_path,
    )

    assert results_1 != results_3
