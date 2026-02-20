from unittest.mock import patch

from owlroost.hydra.trial_worker import run_trial

# ============================================================
# Directory + Basic Execution
# ============================================================


def test_run_trial_creates_directory(tmp_path):
    job_id = "job"
    trial_id = 3
    rates_seed = 111
    longevity_seed = 222

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]
""")

    base_overrides = {}
    run_dir = tmp_path

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        result = run_trial(
            job_id=job_id,
            trial_id=trial_id,
            rates_seed=rates_seed,
            longevity_seed=longevity_seed,
            case_file=case_file,
            base_overrides=base_overrides,
            run_dir=run_dir,
            master_seed=123,
        )

    trial_dir = tmp_path / "trials" / "0003"
    assert trial_dir.exists()
    assert result["trial_id"] == trial_id
    assert result["status"] == "solved"


# ============================================================
# Rate Seed Injection
# ============================================================


def test_rates_seed_injected(tmp_path):
    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]
""")

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        run_trial(
            job_id="job",
            trial_id=0,
            rates_seed=1234,
            longevity_seed=None,
            case_file=case_file,
            base_overrides={},
            run_dir=tmp_path,
            master_seed=123,
        )

        overrides = mock_run.call_args.kwargs["overrides"]

        assert overrides["rates_selection"]["rate_seed"] == 1234
        assert overrides["rates_selection"]["reproducible_rates"] is True


# ============================================================
# Longevity Overwrite Behavior
# ============================================================


@patch("owlroost.hydra.trial_worker.sample_individual_lifetime")
def test_longevity_override_applied(mock_sample, tmp_path):
    mock_sample.return_value = 90

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[longevity]
health = ["average"]
sex = ["female"]
smoker = [false]
partnered = false
""")

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        result = run_trial(
            job_id="job",
            trial_id=0,
            rates_seed=None,
            longevity_seed=999,
            case_file=case_file,
            base_overrides={"longevity": {}},
            run_dir=tmp_path,
            master_seed=123,
            longevity_cfg={"apply_to_plan": True},
        )

        overrides = mock_run.call_args.kwargs["overrides"]

        assert result["status"] == "solved"
        assert overrides["basic_info"]["life_expectancy"] == [90]


@patch("owlroost.hydra.trial_worker.sample_individual_lifetime")
def test_longevity_defaults_used_when_section_missing(mock_sample, tmp_path):
    mock_sample.return_value = 95

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]
""")

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        run_trial(
            job_id="job",
            trial_id=1,
            rates_seed=None,
            longevity_seed=777,
            case_file=case_file,
            base_overrides={"longevity": {}},
            run_dir=tmp_path,
            master_seed=123,
            longevity_cfg={"apply_to_plan": True},
        )

        overrides = mock_run.call_args.kwargs["overrides"]

        assert overrides["basic_info"]["life_expectancy"] == [95]

        _, kwargs = mock_sample.call_args
        assert kwargs["health"] == "average"
        assert kwargs["sex"] == "female"
        assert kwargs["smoker"] is False
        assert kwargs["partnered"] is False


@patch("owlroost.hydra.trial_worker.sample_individual_lifetime")
def test_longevity_defaults_two_individuals(mock_sample, tmp_path):
    mock_sample.side_effect = [88, 92]

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65, 60]
""")

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        run_trial(
            job_id="job",
            trial_id=2,
            rates_seed=None,
            longevity_seed=555,
            case_file=case_file,
            base_overrides={"longevity": {}},
            run_dir=tmp_path,
            master_seed=123,
            longevity_cfg={"apply_to_plan": True},
        )

        overrides = mock_run.call_args.kwargs["overrides"]

        assert overrides["basic_info"]["life_expectancy"] == [88, 92]
        assert mock_sample.call_count == 2

        for call in mock_sample.call_args_list:
            _, kwargs = call
            assert kwargs["health"] == "average"
            assert kwargs["sex"] == "female"
            assert kwargs["smoker"] is False
            assert kwargs["partnered"] is True


# ============================================================
# Longevity Disabled
# ============================================================


@patch("owlroost.hydra.trial_worker.sample_individual_lifetime")
def test_longevity_not_run_when_not_enabled(mock_sample, tmp_path):
    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]
""")

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        run_trial(
            job_id="job",
            trial_id=0,
            rates_seed=None,
            longevity_seed=999,
            case_file=case_file,
            base_overrides={},
            run_dir=tmp_path,
            master_seed=123,
        )

        mock_sample.assert_not_called()

        overrides = mock_run.call_args.kwargs["overrides"]
        assert "basic_info" not in overrides or "life_expectancy" not in overrides.get(
            "basic_info", {}
        )


# ============================================================
# Deterministic Model Still Injects Rate Seed
# ============================================================


def test_rate_seed_injected_even_if_model_deterministic(tmp_path):
    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[rates_selection]
method = "historical average"
""")

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        run_trial(
            job_id="job",
            trial_id=1,
            rates_seed=12345,
            longevity_seed=None,
            case_file=case_file,
            base_overrides={},
            run_dir=tmp_path,
            master_seed=123,
        )

        overrides = mock_run.call_args.kwargs["overrides"]

        assert overrides["rates_selection"]["rate_seed"] == 12345
        assert overrides["rates_selection"]["reproducible_rates"] is True
