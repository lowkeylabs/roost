import subprocess
from pathlib import Path

from click.testing import CliRunner

from tests.utils import run_cli

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def write_case(tmp_path: Path, method: str) -> Path:
    case_file = tmp_path / "Case.toml"
    case_file.write_text(
        f"""
case_name = "write case sample"
[rates_selection]
method = "{method}"
"""
    )
    return case_file


# ---------------------------------------------------------------------
# 1️⃣ rates=bootstrap_sor allows multi-trial even if case is historical
# ---------------------------------------------------------------------


def test_rate_model_override_allows_trials(tmp_path, monkeypatch):
    case_file = write_case(tmp_path, "historical")
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0),
    )

    runner = CliRunner()

    result = run_cli(
        runner,
        case_file,
        "rates_selection=bootstrap_sor",
        "--trials=10",
    )

    assert result.exit_code == 0


# ---------------------------------------------------------------------
# 2️⃣ longevity=default allows multi-trial even if rates are historical
# ---------------------------------------------------------------------


def test_longevity_model_allows_trials(tmp_path, monkeypatch):
    case_file = write_case(tmp_path, "historical")
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0),
    )

    runner = CliRunner()

    result = run_cli(
        runner,
        case_file,
        "longevity=default",
        "--trials=10",
    )

    assert result.exit_code == 0


# ---------------------------------------------------------------------
# 3️⃣ bootstrap_sor without --trials → OK
# ---------------------------------------------------------------------


def test_stochastic_rate_without_trials_flag(tmp_path, monkeypatch):
    case_file = write_case(tmp_path, "bootstrap_sor")
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0),
    )

    runner = CliRunner()

    result = run_cli(runner, case_file)

    assert result.exit_code == 0


# ---------------------------------------------------------------------
# 4️⃣ longevity=default without --trials → OK
# ---------------------------------------------------------------------


def test_longevity_without_trials_flag(tmp_path, monkeypatch):
    case_file = write_case(tmp_path, "historical")
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0),
    )

    runner = CliRunner()

    result = run_cli(
        runner,
        case_file,
        "longevity=default",
    )

    assert result.exit_code == 0


# ---------------------------------------------------------------------
# 5️⃣ rates + longevity together allow multi-trial
# ---------------------------------------------------------------------


def test_rates_and_longevity_with_trials(tmp_path, monkeypatch):
    case_file = write_case(tmp_path, "bootstrap_sor")
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0),
    )

    runner = CliRunner()

    result = run_cli(
        runner,
        case_file,
        "longevity=default",
        "--trials=25",
    )

    assert result.exit_code == 0
