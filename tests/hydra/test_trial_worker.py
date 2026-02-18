from pathlib import Path
from unittest.mock import patch

from owlroost.hydra.trial_worker import run_trial


def test_run_trial_creates_directory(tmp_path):
    job_id = "job"
    trial_id = 3
    rates_seed = 111
    longevity_seed = 222

    # Minimal TOML stub
    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[roost]
use_longevity_model = false
""")

    base_overrides = {}
    run_dir = tmp_path

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        result = run_trial(
            job_id,
            trial_id,
            rates_seed,
            longevity_seed,
            case_file,
            base_overrides,
            run_dir,
        )

    trial_dir = tmp_path / "trials" / "0003"
    assert trial_dir.exists()
    assert result["trial_id"] == trial_id
    assert result["status"] == "solved"


def test_rates_seed_injected(tmp_path):
    job_id = "job"
    trial_id = 0
    rates_seed = 1234
    longevity_seed = None

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[roost]
use_longevity_model = false
""")

    base_overrides = {}
    run_dir = tmp_path

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        run_trial(
            job_id,
            trial_id,
            rates_seed,
            longevity_seed,
            case_file,
            base_overrides,
            run_dir,
        )

        called_kwargs = mock_run.call_args.kwargs
        assert called_kwargs["overrides"]["rates"]["rate_seed"] == rates_seed

@patch("owlroost.hydra.trial_worker.sample_individual_lifetime")
def test_longevity_override_applied(mock_sample, tmp_path):
    mock_sample.return_value = 90

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[roost]
use_longevity_model = true

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
            base_overrides={},
            run_dir=tmp_path,
        )

        called_kwargs = mock_run.call_args.kwargs
        assert called_kwargs["overrides"]["basic_info"]["life_expectancy"] == [90]
        assert called_kwargs["overrides"]["longevity"]["longevity_seed"] == 999

@patch("owlroost.hydra.trial_worker.sample_individual_lifetime")
def test_longevity_defaults_used_when_section_missing(mock_sample, tmp_path):
    """
    If use_longevity_model is true but no [longevity] section
    exists, defaults should be used and overrides injected.
    """
    mock_sample.return_value = 95

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[roost]
use_longevity_model = true
""")

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        run_trial(
            job_id="job",
            trial_id=1,
            rates_seed=None,
            longevity_seed=777,
            case_file=case_file,
            base_overrides={},
            run_dir=tmp_path,
        )

        called_kwargs = mock_run.call_args.kwargs
        overrides = called_kwargs["overrides"]

        # Life expectancy should be overridden from sampled value
        assert overrides["basic_info"]["life_expectancy"] == [95]

        # Longevity seed should be recorded
        assert overrides["longevity"]["longevity_seed"] == 777

        # Ensure sample was called with defaults
        args, kwargs = mock_sample.call_args
        assert kwargs["health"] == "average"
        assert kwargs["sex"] == "female"
        assert kwargs["smoker"] is False
        assert kwargs["partnered"] is False


@patch("owlroost.hydra.trial_worker.sample_individual_lifetime")
def test_longevity_defaults_two_individuals(mock_sample, tmp_path):
    """
    If use_longevity_model is true and there are two individuals
    but no [longevity] section exists, defaults should be applied
    per individual and two values generated.
    """

    # Return two different values for two calls
    mock_sample.side_effect = [88, 92]

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65, 60]

[roost]
use_longevity_model = true
""")

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        run_trial(
            job_id="job",
            trial_id=2,
            rates_seed=None,
            longevity_seed=555,
            case_file=case_file,
            base_overrides={},
            run_dir=tmp_path,
        )

        called_kwargs = mock_run.call_args.kwargs
        overrides = called_kwargs["overrides"]

        # Two sampled life expectancies applied
        assert overrides["basic_info"]["life_expectancy"] == [88, 92]

        # Longevity seed stored
        assert overrides["longevity"]["longevity_seed"] == 555

        # Ensure sampling called twice
        assert mock_sample.call_count == 2

        # Verify default arguments used per individual
        calls = mock_sample.call_args_list

        for call in calls:
            _, kwargs = call
            assert kwargs["health"] == "average"
            assert kwargs["sex"] == "female"
            assert kwargs["smoker"] is False
            assert kwargs["partnered"] is True


@patch("owlroost.hydra.trial_worker.sample_individual_lifetime")
def test_longevity_not_run_when_flag_false(mock_sample, tmp_path):
    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[roost]
use_longevity_model = false
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
        )

        # Longevity function should never be called
        mock_sample.assert_not_called()

        overrides = mock_run.call_args.kwargs["overrides"]

        assert "basic_info" not in overrides or \
               "life_expectancy" not in overrides.get("basic_info", {})

        assert "longevity" not in overrides

def test_rate_seed_always_injected_for_multi_trial(tmp_path):
    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[rates_selection]
method = "historical average"

[roost]
use_longevity_model = false
use_bootstrap_model = false
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
        )

        overrides = mock_run.call_args.kwargs["overrides"]

        assert overrides["rates"]["rate_seed"] == 12345

def test_reproducible_rates_flag_set(tmp_path):
    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[rates_selection]
method = "historical average"

[roost]
use_longevity_model = false
use_bootstrap_model = false
""")

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        run_trial(
            job_id="job",
            trial_id=1,
            rates_seed=999,
            longevity_seed=None,
            case_file=case_file,
            base_overrides={},
            run_dir=tmp_path,
        )

        overrides = mock_run.call_args.kwargs["overrides"]

        assert overrides["rates"]["reproducible_rates"] is True

def test_bootstrap_model_overrides_rates(tmp_path):
    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]

[rates_selection]
method = "historical average"

[roost]
use_bootstrap_model = true
""")

    with patch("owlroost.hydra.trial_worker.run_single_case") as mock_run:
        mock_run.return_value.status = "solved"

        run_trial(
            job_id="job",
            trial_id=2,
            rates_seed=777,
            longevity_seed=None,
            case_file=case_file,
            base_overrides={},
            run_dir=tmp_path,
        )

        overrides = mock_run.call_args.kwargs["overrides"]
        rates = overrides["rates"]

        assert rates["method"] == "bootstrap_sor"
        assert rates["bootstrap_type"] == "block"
        assert rates["block_size"] == 7
        assert rates["frm"] == 1928
        assert rates["to"] == 2025
        assert rates["rate_seed"] == 777
        assert rates["reproducible_rates"] is True
