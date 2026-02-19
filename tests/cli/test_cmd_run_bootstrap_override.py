import subprocess
from pathlib import Path

from click.testing import CliRunner

from owlroost.cli.cmd_run import cmd_run


def test_bootstrap_override_allows_trials(tmp_path, monkeypatch):
    """
    Desired behavior:

    If override roost.use_bootstrap_model is provided,
    validation should allow multi-trial execution even if
    case file says method = historical.
    """

    case_file = tmp_path / "Case_9.toml"
    case_file.write_text(
        """
[rates_selection]
method = "historical"
"""
    )

    monkeypatch.chdir(tmp_path)

    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()

    result = runner.invoke(
        cmd_run,
        [
            "Case_9.toml",
            "roost.use_bootstrap_model",
            "--trials=10",
        ],
    )

    # 🔴 This is what we WANT to happen
    assert result.exit_code == 0

def test_longevity_override_allows_trials(tmp_path, monkeypatch):
    """
    If override roost.use_longevity_model is provided,
    multi-trial execution should succeed even if
    case file uses deterministic rates.
    """

    case_file = tmp_path / "Case_9.toml"
    case_file.write_text(
        """
[rates_selection]
method = "historical"
"""
    )

    monkeypatch.chdir(tmp_path)

    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()

    result = runner.invoke(
        cmd_run,
        [
            "Case_9.toml",
            "roost.use_longevity_model",
            "--trials=10",
        ],
    )

    assert result.exit_code == 0


def test_stochastic_rate_without_trials_flag(tmp_path, monkeypatch):
    """
    A stochastic rate model should run even without --trials.
    """

    case_file = tmp_path / "Case.toml"
    case_file.write_text(
        """
[rates_selection]
method = "bootstrap_sor"
"""
    )

    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0),
    )

    runner = CliRunner()

    result = runner.invoke(cmd_run, ["Case.toml"])

    assert result.exit_code == 0


def test_longevity_override_without_trials_flag(tmp_path, monkeypatch):
    """
    Longevity override should run even without --trials.
    """

    case_file = tmp_path / "Case.toml"
    case_file.write_text(
        """
[rates_selection]
method = "historical"
"""
    )

    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0),
    )

    runner = CliRunner()

    result = runner.invoke(
        cmd_run,
        ["Case.toml", "roost.use_longevity_model"],
    )

    assert result.exit_code == 0

def test_rates_and_longevity_with_trials(tmp_path, monkeypatch):
    """
    If both stochastic rate model and longevity override are active,
    multi-trial execution should succeed.
    """

    case_file = tmp_path / "Case.toml"
    case_file.write_text(
        """
[rates_selection]
method = "bootstrap_sor"
"""
    )

    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0),
    )

    runner = CliRunner()

    result = runner.invoke(
        cmd_run,
        [
            "Case.toml",
            "roost.use_longevity_model",
            "--trials=25",
        ],
    )

    assert result.exit_code == 0

def test_deterministic_without_any_stochastic_blocks_trials(tmp_path):
    """
    Deterministic rates and no longevity override
    should block multi-trial execution.
    """

    case_file = tmp_path / "Case.toml"
    case_file.write_text(
        """
[rates_selection]
method = "historical"
"""
    )

    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("Case.toml").write_text(case_file.read_text())

        result = runner.invoke(
            cmd_run,
            ["Case.toml", "--trials=10"],
        )

        assert result.exit_code != 0
