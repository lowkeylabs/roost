import subprocess
from pathlib import Path

from click.testing import CliRunner

from tests.utils import run_cli

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


class FakeProcess:
    def __init__(self, cmd, called):
        called["cmd"] = cmd
        self.returncode = 0

    def wait(self):
        return self.returncode


def mock_popen(monkeypatch, called):
    class FakeProcess:
        def __init__(self, cmd):
            called["cmd"] = cmd
            self.returncode = 0

        def wait(self):
            return self.returncode

    def fake_popen(cmd, *args, **kwargs):
        return FakeProcess(cmd)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)


def mock_monitor(monkeypatch):
    def fake_monitor(run_root, total_trials):
        class DummyThread:
            def join(self):
                pass

        return DummyThread(), Path("dummy.log")

    monkeypatch.setattr("owlroost.cli.cmd_run.start_progress_monitor", fake_monitor)

    # 🔥 THIS IS THE CRITICAL FIX
    monkeypatch.setattr(
        "owlroost.cli.cmd_run.read_progress",
        lambda _: 10**9,  # always "complete"
    )


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
    mock_popen(monkeypatch, called)
    mock_monitor(monkeypatch)

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
    mock_popen(monkeypatch, called)
    mock_monitor(monkeypatch)

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
    mock_popen(monkeypatch, called)
    mock_monitor(monkeypatch)

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
    mock_popen(monkeypatch, called)
    mock_monitor(monkeypatch)

    runner = CliRunner()

    result = run_cli(
        runner,
        case_file,
        "-t",
        "5",
        "optimization_parameters.objective=maxBequest",
        "solver_options.maxRothConversion=50",
    )

    assert result.exit_code == 0

    cmd_str = " ".join(called["cmd"])
    assert "optimization_parameters.objective=maxBequest" in cmd_str
    assert "solver_options.maxRothConversion=50" in cmd_str


# ---------------------------------------------------------------------
# 5️⃣ trial-id injection
# ---------------------------------------------------------------------


def test_trial_id_injection(tmp_path, monkeypatch):
    case_file = write_case(tmp_path, "stochastic")
    monkeypatch.chdir(tmp_path)

    called = {}
    mock_popen(monkeypatch, called)
    mock_monitor(monkeypatch)

    monkeypatch.setattr(
        "owlroost.hydra.owl_hydra_run.orchestrate_trials", lambda *args, **kwargs: []
    )

    runner = CliRunner()

    result = run_cli(
        runner,
        case_file,
        "--trial-id",
        "7",
    )

    assert result.exit_code == 0
    assert "trial.id=7" in " ".join(called["cmd"])
