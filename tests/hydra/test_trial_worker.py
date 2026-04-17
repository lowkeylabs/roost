from types import SimpleNamespace
from unittest.mock import patch

from owlroost.hydra.trial_worker import run_trial

# ============================================================
# Directory + Basic Execution
# ============================================================


def create_metrics_file(trial_dir, case_stem):
    metrics_path = trial_dir / f"{case_stem}_metrics.json"
    metrics_path.write_text(
        """
{
  "schema": "roost.metrics.v2",
  "run_status": {
    "status": "solved"
  }
}
"""
    )


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

    with patch("owlroost.hydra.trial_worker.run_single_case_subprocess") as mock_run:
        mock_run.return_value = SimpleNamespace(status="solved")

        trial_dir = tmp_path / "trials" / "0003"
        trial_dir.mkdir(parents=True, exist_ok=True)

        create_metrics_file(trial_dir, case_file.stem)

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

    with patch("owlroost.hydra.trial_worker.run_single_case_subprocess") as mock_run:
        mock_run.return_value = SimpleNamespace(status="solved")

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

        args = mock_run.call_args.args[0]
        overrides = args["overrides"]

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

    with patch("owlroost.hydra.trial_worker.run_single_case_subprocess") as mock_run:
        mock_run.return_value = SimpleNamespace(status="solved")

        trial_dir = tmp_path / "trials" / "0000"
        trial_dir.mkdir(parents=True, exist_ok=True)

        create_metrics_file(trial_dir, case_file.stem)

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

        args = mock_run.call_args.args[0]
        overrides = args["overrides"]

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

    with patch("owlroost.hydra.trial_worker.run_single_case_subprocess") as mock_run:
        mock_run.return_value = SimpleNamespace(status="solved")

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

        args = mock_run.call_args.args[0]
        overrides = args["overrides"]

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

    with patch("owlroost.hydra.trial_worker.run_single_case_subprocess") as mock_run:
        mock_run.return_value = SimpleNamespace(status="solved")

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

        args = mock_run.call_args.args[0]
        overrides = args["overrides"]

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

    with patch("owlroost.hydra.trial_worker.run_single_case_subprocess") as mock_run:
        mock_run.return_value = SimpleNamespace(status="solved")

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

        args = mock_run.call_args.args[0]
        overrides = args["overrides"]

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

    with patch("owlroost.hydra.trial_worker.run_single_case_subprocess") as mock_run:
        mock_run.return_value = SimpleNamespace(status="solved")

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

        args = mock_run.call_args.args[0]
        overrides = args["overrides"]

        assert overrides["rates_selection"]["rate_seed"] == 12345
        assert overrides["rates_selection"]["reproducible_rates"] is True


# ============================================================
# Subprocess Behavior
# ============================================================


def test_run_trial_subprocess_success(tmp_path, monkeypatch):
    """run_trial should propagate success from subprocess wrapper"""

    def mock_subprocess(*args, **kwargs):
        return SimpleNamespace(status="solved", output_file="dummy.xlsx")

    monkeypatch.setattr(
        "owlroost.hydra.trial_worker.run_single_case_subprocess",
        mock_subprocess,
    )

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]
""")

    trial_dir = tmp_path / "trials" / "0000"
    trial_dir.mkdir(parents=True, exist_ok=True)

    create_metrics_file(trial_dir, case_file.stem)

    result = run_trial(
        job_id="job",
        trial_id=0,
        rates_seed=None,
        longevity_seed=None,
        case_file=case_file,
        base_overrides={},
        run_dir=tmp_path,
        master_seed=123,
    )

    assert result["status"] == "solved"


def test_run_trial_subprocess_crash(tmp_path, monkeypatch):
    """run_trial should convert subprocess crash into status='crashed'"""

    def mock_subprocess(*args, **kwargs):
        return SimpleNamespace(status="failed")

    monkeypatch.setattr(
        "owlroost.hydra.trial_worker.run_single_case_subprocess",
        mock_subprocess,
    )

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]
""")

    trial_dir = tmp_path / "trials" / "0000"
    trial_dir.mkdir(parents=True, exist_ok=True)

    create_metrics_file(trial_dir, case_file.stem)

    result = run_trial(
        job_id="job",
        trial_id=1,
        rates_seed=None,
        longevity_seed=None,
        case_file=case_file,
        base_overrides={},
        run_dir=tmp_path,
        master_seed=123,
    )

    assert result["status"] == "failed"
    assert result["output"] is None


def test_subprocess_args_structure(tmp_path, monkeypatch):
    """Ensure run_trial sends correct args into subprocess"""

    captured = {}

    def mock_subprocess(*args, **kwargs):
        captured.update(args[0])
        return SimpleNamespace(status="solved")

    monkeypatch.setattr(
        "owlroost.hydra.trial_worker.run_single_case_subprocess",
        mock_subprocess,
    )

    case_file = tmp_path / "case.toml"
    case_file.write_text("""
[basic_info]
life_expectancy = [65]
""")

    run_trial(
        job_id="job",
        trial_id=3,
        rates_seed=42,
        longevity_seed=99,
        case_file=case_file,
        base_overrides={},
        run_dir=tmp_path,
        master_seed=123,
    )

    assert captured["case_file"] == str(case_file)
    assert "overrides" in captured
    assert "roost_runtime" in captured
