from __future__ import annotations

import json
from pathlib import Path

from ..models.results import Experiment, Run, Trial

# =========================================================
# Discovery (unchanged)
# =========================================================


def discover_experiments(results_dir) -> list[Experiment]:
    experiments: list[Experiment] = []
    exp_id = 0

    for case_dir in sorted(p for p in results_dir.iterdir() if p.is_dir()):
        for date_dir in sorted(p for p in case_dir.iterdir() if p.is_dir()):
            for time_dir in sorted(p for p in date_dir.iterdir() if p.is_dir()):
                runs: list[Run] = []

                for run_dir in sorted(
                    p for p in time_dir.iterdir() if p.is_dir() and p.name.startswith("run_")
                ):
                    trials: list[Trial] = []
                    trials_dir = run_dir / "trials"

                    if trials_dir.exists():
                        for trial_dir in sorted(p for p in trials_dir.iterdir() if p.is_dir()):
                            data = extract_trial_data(trial_dir)

                            trials.append(
                                Trial(
                                    path=trial_dir,
                                    status=get_trial_status(trial_dir),
                                    runtime=(
                                        data.get("timing", {}).get("elapsed_seconds")
                                        if data
                                        else None
                                    ),
                                    data=data,
                                )
                            )

                    runs.append(Run(run_dir.name, run_dir, trials))

                experiments.append(
                    Experiment(
                        id=exp_id,
                        case=case_dir.name,
                        date=date_dir.name,
                        time=time_dir.name,
                        path=time_dir,
                        runs=runs,
                    )
                )

                exp_id += 1

    return experiments


# =========================================================
# Trial Helpers (unchanged)
# =========================================================


def get_trial_status(trial_dir: Path) -> str:
    if (trial_dir / "SOLVED").exists():
        return "SOLVED"
    if (trial_dir / "UNSUCCESSFUL").exists():
        return "FAILED"
    return "INCOMPLETE"


def extract_trial_data(trial_dir: Path) -> dict | None:
    """
    Load full *_metrics.json WITHOUT flattening.

    This preserves:
        - run_status
        - metrics
        - complexity
        - timing
    """
    metrics_file = next(trial_dir.glob("*_metrics.json"), None)
    if not metrics_file:
        return None

    try:
        with metrics_file.open() as f:
            return json.load(f)

    except Exception:
        return None
