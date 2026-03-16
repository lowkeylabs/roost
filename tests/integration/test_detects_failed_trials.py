import multiprocessing as mp

import pytest

from owlroost.hydra.owl_hydra_run import orchestrate_trials


def _orchestrator_entry(args):
    """Entry point executed in a subprocess."""

    orchestrate_trials(**args)


def test_orchestrate_trials_deadlocks_on_worker_exception(monkeypatch, tmp_path):
    """
    Strong integration test that reproduces the real multiprocessing deadlock.

    A worker raises an exception. Because apply_async callbacks are not executed
    on failure, the orchestrator progress loop never completes.

    The test detects this by running the orchestrator in a subprocess and
    verifying that it never exits.
    """

    # -----------------------------
    # Fake worker that crashes
    # -----------------------------
    def fake_run_trial(
        job_id,
        trial_id,
        rates_seed,
        longevity_seed,
        case_file,
        overrides,
        run_dir,
        master_seed,
        longevity_cfg,
    ):
        if trial_id == 1:
            raise RuntimeError("Simulated OWL crash")

        return {
            "trial_id": trial_id,
            "rates_seed": rates_seed,
            "longevity_seed": longevity_seed,
            "status": "solved",
            "output": "fake.xlsx",
        }

    monkeypatch.setattr(
        "owlroost.hydra.owl_hydra_run.run_trial",
        fake_run_trial,
    )

    # -----------------------------
    # Minimal run configuration
    # -----------------------------
    case_file = tmp_path / "case.toml"
    case_file.write_text("dummy = true")

    args = dict(
        job_id="test_job",
        master_seed=1234,
        trial_ids=[0, 1],
        use_trial_seeds=True,
        n_jobs=2,
        case_file=case_file,
        overrides={},
        run_dir=tmp_path,
        longevity_cfg={},
    )

    # -----------------------------
    # Run orchestrator in subprocess
    # -----------------------------
    ctx = mp.get_context("spawn")
    p = ctx.Process(target=_orchestrator_entry, args=(args,))
    p.start()

    p.join(timeout=5)

    if p.is_alive():
        p.terminate()
        p.join()

        pytest.fail("orchestrate_trials deadlocked when a worker raised an exception.")
