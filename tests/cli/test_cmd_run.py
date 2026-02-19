import subprocess
from pathlib import Path

from click.testing import CliRunner

from owlroost.cli.cmd_run import cmd_run

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
    _case_file = write_case(tmp_path, "historical")

    monkeypatch.chdir(tmp_path)

    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()
    result = runner.invoke(cmd_run, ["Case_test.toml"])

    assert result.exit_code == 0
    assert "case.file=" in " ".join(called["cmd"])


# ---------------------------------------------------------------------
# 2️⃣ Historical + multi-trial → FAIL
# ---------------------------------------------------------------------


def test_historical_multiple_trials_fails(tmp_path):
    case_file = write_case(tmp_path, "historical")

    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("Case_test.toml").write_text(case_file.read_text())

        result = runner.invoke(cmd_run, ["Case_test.toml", "-t", "10"])

        assert result.exit_code != 0
        assert "stochastic" in result.output.lower()


# ---------------------------------------------------------------------
# 3️⃣ Stochastic + multi-trial → OK
# ---------------------------------------------------------------------


def test_stochastic_multiple_trials_ok(tmp_path, monkeypatch):
    _case_file = write_case(tmp_path, "stochastic")
    monkeypatch.chdir(tmp_path)

    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()
    result = runner.invoke(cmd_run, ["Case_test.toml", "-t", "10"])

    assert result.exit_code == 0

    cmd_str = " ".join(called["cmd"])
    assert "trial.count=10" in cmd_str


# ---------------------------------------------------------------------
# 4️⃣ Hydra overrides pass through
# ---------------------------------------------------------------------


def test_hydra_override_passthrough(tmp_path, monkeypatch):
    _case_file = write_case(tmp_path, "stochastic")
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
            "Case_test.toml",
            "-t",
            "5",
            "optimization.objective=maxBequest",
            "solver_options.maxRothConversion=50",
        ],
    )

    assert result.exit_code == 0

    cmd_str = " ".join(called["cmd"])

    assert "optimization.objective=maxBequest" in cmd_str
    assert "solver_options.maxRothConversion=50" in cmd_str


# ---------------------------------------------------------------------
# 5️⃣ trial-id injection
# ---------------------------------------------------------------------


def test_trial_id_injection(tmp_path, monkeypatch):
    _case_file = write_case(tmp_path, "stochastic")
    monkeypatch.chdir(tmp_path)

    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()

    result = runner.invoke(
        cmd_run,
        ["Case_test.toml", "--trial-id", "7"],
    )

    assert result.exit_code == 0

    cmd_str = " ".join(called["cmd"])
    assert "trial.id=7" in cmd_str


# ---------------------------------------------------------------------
# 6️⃣ bootstrap model allows multi-trial
# ---------------------------------------------------------------------


def test_bootstrap_model_allows_multi_trial(tmp_path, monkeypatch):
    _case_file = write_case(tmp_path, "bootstrap_sor")
    monkeypatch.chdir(tmp_path)

    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = CliRunner()

    result = runner.invoke(cmd_run, ["Case_test.toml", "-t", "3"])

    assert result.exit_code == 0
