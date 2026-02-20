import subprocess
from pathlib import Path

from click.testing import CliRunner

from tests.utils import run_cli

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def write_case(tmp_path: Path, method: str) -> Path:
    case_file = tmp_path / "Case_test.toml"
    case_file.write_text(
        f"""
[rates_selection]
method = "{method}"
"""
    )
    return case_file


# ---------------------------------------------------------------------
# 1️⃣ Historical + single run → OK
# ---------------------------------------------------------------------


def test_historical_single_run_ok(tmp_path, monkeypatch):
    case_file = write_case(tmp_path, "historical")
    monkeypatch.chdir(tmp_path)

    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()
    result = run_cli(runner, case_file)

    assert result.exit_code == 0
    assert "case.file=" in " ".join(called["cmd"])


# ---------------------------------------------------------------------
# 2️⃣ Historical + multi-trial → OK (deterministic allowed)
# ---------------------------------------------------------------------


def test_historical_multiple_trials_ok(tmp_path, monkeypatch):
    case_file = write_case(tmp_path, "historical")
    monkeypatch.chdir(tmp_path)

    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()
    result = run_cli(runner, case_file, "-t", "10")

    assert result.exit_code == 0
    assert "trial.count=10" in " ".join(called["cmd"])


# ---------------------------------------------------------------------
# 3️⃣ Stochastic + multi-trial → OK
# ---------------------------------------------------------------------


def test_stochastic_multiple_trials_ok(tmp_path, monkeypatch):
    case_file = write_case(tmp_path, "stochastic")
    monkeypatch.chdir(tmp_path)

    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()
    result = run_cli(runner, case_file, "-t", "10")

    assert result.exit_code == 0
    assert "trial.count=10" in " ".join(called["cmd"])


# ---------------------------------------------------------------------
# 4️⃣ Hydra overrides pass through
# ---------------------------------------------------------------------


def test_hydra_override_passthrough(tmp_path, monkeypatch):
    case_file = write_case(tmp_path, "stochastic")
    monkeypatch.chdir(tmp_path)

    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()

    result = run_cli(
        runner,
        case_file,
        "-t",
        "5",
        "optimization.objective=maxBequest",
        "solver_options.maxRothConversion=50",
    )

    assert result.exit_code == 0

    cmd_str = " ".join(called["cmd"])
    assert "optimization.objective=maxBequest" in cmd_str
    assert "solver_options.maxRothConversion=50" in cmd_str


# ---------------------------------------------------------------------
# 5️⃣ trial-id injection
# ---------------------------------------------------------------------


def test_trial_id_injection(tmp_path, monkeypatch):
    case_file = write_case(tmp_path, "stochastic")
    monkeypatch.chdir(tmp_path)

    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()

    result = run_cli(
        runner,
        case_file,
        "--trial-id",
        "7",
    )

    assert result.exit_code == 0
    assert "trial.id=7" in " ".join(called["cmd"])
