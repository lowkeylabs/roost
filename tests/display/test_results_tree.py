# tests/display/test_results_tree.py

from pathlib import Path

from owlroost.display.discovery import (
    find_all_runs,
    find_cases,
    find_first_trial,
    find_pending_trials,
    find_runs,
    find_sessions,
    find_trials,
    has_metrics,
    summarize_run,
)


# =========================================================
# Helpers
# =========================================================
def make_trial(trials_dir: Path, name: str, metrics=True):
    td = trials_dir / name
    td.mkdir(parents=True)

    (td / "trial.toml").write_text("x=1")

    if metrics:
        (td / "metrics.json").write_text("{}")

    return td


def make_run(exp_dir: Path, run_name="run_0", completed=2, pending=1):
    run_dir = exp_dir / run_name
    run_dir.mkdir(parents=True)

    trials_dir = run_dir / "trials"
    trials_dir.mkdir()

    idx = 0

    for _ in range(completed):
        make_trial(trials_dir, f"{idx:04d}", metrics=True)
        idx += 1

    for _ in range(pending):
        make_trial(trials_dir, f"{idx:04d}", metrics=False)
        idx += 1

    return run_dir


def make_session(case_dir: Path, date, time):
    exp_dir = case_dir / date / time
    exp_dir.mkdir(parents=True)

    (exp_dir / "multirun.yaml").write_text("x: 1")

    return exp_dir


# =========================================================
# find_cases
# =========================================================
def test_find_cases(tmp_path):
    results = tmp_path / "results"
    results.mkdir()

    (results / "case_a").mkdir()
    (results / "case_b").mkdir()

    cases = find_cases(results)

    assert len(cases) == 2

    names = [p.name for p in cases]

    assert names == ["case_a", "case_b"]


# =========================================================
# find_sessions
# =========================================================
def test_find_sessions(tmp_path):
    results = tmp_path / "results"
    results.mkdir()

    case_dir = results / "case_a"
    case_dir.mkdir()

    exp1 = make_session(case_dir, "2026-05-05", "08-00-00")
    exp2 = make_session(case_dir, "2026-05-05", "09-00-00")

    sessions = find_sessions(results)

    assert len(sessions) == 2

    assert exp1.resolve() in sessions
    assert exp2.resolve() in sessions


def test_find_sessions_ignores_non_sessions(tmp_path):
    results = tmp_path / "results"
    results.mkdir()

    case_dir = results / "case_a"
    case_dir.mkdir()

    junk = case_dir / "2026-05-05" / "not_an_session"
    junk.mkdir(parents=True)

    sessions = find_sessions(results)

    assert sessions == []


# =========================================================
# find_runs
# =========================================================
def test_find_runs(tmp_path):
    results = tmp_path / "results"
    results.mkdir()

    case_dir = results / "case_a"
    case_dir.mkdir()

    exp_dir = make_session(case_dir, "2026-05-05", "08-00-00")

    run0 = exp_dir / "run_0"
    run1 = exp_dir / "run_1"

    run0.mkdir()
    run1.mkdir()

    runs = find_runs(exp_dir)

    assert len(runs) == 2

    assert run0.resolve() in runs
    assert run1.resolve() in runs


# =========================================================
# find_trials
# =========================================================
def test_find_trials(tmp_path):
    results = tmp_path / "results"
    results.mkdir()

    case_dir = results / "case_a"
    case_dir.mkdir()

    exp_dir = make_session(case_dir, "2026-05-05", "08-00-00")

    run_dir = make_run(exp_dir, completed=2, pending=1)

    trials = find_trials(run_dir)

    assert len(trials) == 3

    names = [p.name for p in trials]

    assert names == ["0000", "0001", "0002"]


# =========================================================
# find_first_trial
# =========================================================
def test_find_first_trial(tmp_path):
    results = tmp_path / "results"
    results.mkdir()

    case_dir = results / "case_a"
    case_dir.mkdir()

    exp_dir = make_session(case_dir, "2026-05-05", "08-00-00")

    run_dir = make_run(exp_dir, completed=3, pending=0)

    first = find_first_trial(run_dir)

    assert first is not None
    assert first.name == "0000"


def test_find_first_trial_empty(tmp_path):
    run_dir = tmp_path / "run_0"
    run_dir.mkdir()

    (run_dir / "trials").mkdir()

    first = find_first_trial(run_dir)

    assert first is None


# =========================================================
# has_metrics
# =========================================================
def test_has_metrics_true(tmp_path):
    td = tmp_path / "0000"
    td.mkdir()

    (td / "metrics.json").write_text("{}")

    assert has_metrics(td) is True


def test_has_metrics_false(tmp_path):
    td = tmp_path / "0000"
    td.mkdir()

    assert has_metrics(td) is False


# =========================================================
# summarize_run
# =========================================================
def test_summarize_run(tmp_path):
    results = tmp_path / "results"
    results.mkdir()

    case_dir = results / "case_a"
    case_dir.mkdir()

    exp_dir = make_session(case_dir, "2026-05-05", "08-00-00")

    run_dir = make_run(
        exp_dir,
        completed=4,
        pending=2,
    )

    summary = summarize_run(run_dir)

    assert summary["total"] == 6
    assert summary["completed"] == 4
    assert summary["pending"] == 2


# =========================================================
# find_all_runs
# =========================================================
def test_find_all_runs(tmp_path):
    results = tmp_path / "results"
    results.mkdir()

    case_a = results / "case_a"
    case_b = results / "case_b"

    case_a.mkdir()
    case_b.mkdir()

    exp1 = make_session(case_a, "2026-05-05", "08-00-00")
    exp2 = make_session(case_b, "2026-05-06", "09-00-00")

    make_run(exp1, run_name="run_0")
    make_run(exp1, run_name="run_1")
    make_run(exp2, run_name="run_0")

    runs = find_all_runs(results)

    assert len(runs) == 3


# =========================================================
# find_pending_trials
# =========================================================
def test_find_pending_trials(tmp_path):
    results = tmp_path / "results"
    results.mkdir()

    case_dir = results / "case_a"
    case_dir.mkdir()

    exp_dir = make_session(case_dir, "2026-05-05", "08-00-00")

    make_run(
        exp_dir,
        completed=3,
        pending=2,
    )

    pending = find_pending_trials(results)

    assert len(pending) == 2

    names = [p.name for p in pending]

    assert names == ["0003", "0004"]


# =========================================================
# robustness
# =========================================================
def test_missing_results_dir(tmp_path):
    missing = tmp_path / "missing"

    assert find_cases(missing) == []
    assert find_sessions(missing) == []
    assert find_all_runs(missing) == []


def test_missing_trials_dir(tmp_path):
    run_dir = tmp_path / "run_0"
    run_dir.mkdir()

    assert find_trials(run_dir) == []

    summary = summarize_run(run_dir)

    assert summary["total"] == 0
    assert summary["completed"] == 0
    assert summary["pending"] == 0
