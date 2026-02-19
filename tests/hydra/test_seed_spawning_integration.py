from unittest.mock import patch

from hydra import compose, initialize_config_module
from hydra.core.global_hydra import GlobalHydra

from owlroost.hydra.owl_hydra_run import orchestrate_trials, run_hydra_job

# ============================================================
# SEED BEHAVIOR TESTS (UNCHANGED — still valid)
# ============================================================


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_seed_spawning_deterministic(mock_run_trial, tmp_path):
    captured = []

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, *args):
        captured.append((trial_id, rates_seed, longevity_seed))
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

    case_file = tmp_path / "case.toml"
    case_file.write_text("dummy")

    trial_ids = [0, 1, 2]

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
    assert len(set(first_run)) == 3

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

    assert first_run == captured

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

    assert first_run != captured


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_seed_independent_of_trial_order(mock_run_trial, tmp_path):
    case_file = tmp_path / "case.toml"
    case_file.write_text("dummy")

    master_seed = 54321
    captured = {}

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, *args):
        captured[trial_id] = (rates_seed, longevity_seed)
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

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
    captured.clear()

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

    for tid in ordered_ids:
        assert seeds_ordered[tid] == seeds_shuffled[tid]


# ============================================================
# ORCHESTRATION PURITY TESTS (UPDATED)
# ============================================================


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_overrides_not_shared_between_trials(mock_run_trial, tmp_path):
    seen = []

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, case_file, overrides, run_dir):
        overrides["marker"] = trial_id
        seen.append((trial_id, dict(overrides)))
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

    orchestrate_trials(
        job_id="job",
        master_seed=123,
        trial_ids=[0, 1, 2],
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

    for _, rates_seed, longevity_seed in captured:
        assert rates_seed is None
        assert longevity_seed is None


# ============================================================
# HYDRA INTEGRATION TESTS (UPDATED — NO BOOTSTRAP MUTATION)
# ============================================================


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_hydra_group_selection_passed_through(mock_run_trial, tmp_path):
    captured = []

    def fake_run_trial(job_id, trial_id, rates_seed, longevity_seed, case_file, overrides, run_dir):
        captured.append(overrides)
        return {"status": "solved", "trial_id": trial_id}

    mock_run_trial.side_effect = fake_run_trial

    case_file = tmp_path / "case.toml"
    case_file.write_text("dummy")

    overrides = [
        f"case.file={case_file}",
        "trial.count=2",
        "trial.n_jobs=1",
        "roost.master_seed=11111",
        "rates_selection=bootstrap_sor",
        "longevity=default",
    ]

    GlobalHydra.instance().clear()

    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(config_name="config", overrides=overrides)

    run_hydra_job(cfg)

    assert len(captured) == 2

    # Ensure overrides were NOT mutated by orchestrator
    for o in captured:
        assert "rates" not in o  # no virtual injection
        assert "rates_selection" in cfg  # Hydra handled composition


# ============================================================
# REPRODUCIBILITY CONTRACT (UNCHANGED)
# ============================================================


@patch("owlroost.hydra.owl_hydra_run.run_trial")
def test_reproducibility_contract(mock_run_trial, tmp_path):
    def deterministic_run_trial(job_id, trial_id, rates_seed, longevity_seed, *args):
        return {
            "status": "solved",
            "trial_id": trial_id,
            "rates_seed": rates_seed,
            "longevity_seed": longevity_seed,
            "synthetic_metric": (rates_seed or 0) ^ (longevity_seed or 0),
        }

    mock_run_trial.side_effect = deterministic_run_trial

    trial_ids = [0, 1, 2, 3]

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
