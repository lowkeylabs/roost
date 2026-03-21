from __future__ import annotations

from owlroost.domain.services.aggregation import aggregate_rows
from owlroost.domain.services.context import enrich_row
from owlroost.domain.services.metrics import build_trial_row

# =========================================================
# RUN ROWS
# =========================================================


def build_run_rows(experiments):
    """
    Build aggregated run-level rows across all experiments.

    Each row represents a run (aggregated from its trials).
    """

    run_rows = []

    for exp_index, exp in enumerate(experiments):
        for run_index, run in enumerate(exp.runs):
            trial_rows = build_trial_rows(exp, run)

            if not trial_rows:
                continue

            summary = aggregate_rows(trial_rows)

            summary["_ref"] = {
                "exp_index": exp_index,
                "run_index": run_index,
            }

            run_rows.append(summary)

    return run_rows


# =========================================================
# TRIAL ROWS
# =========================================================


def build_trial_rows(exp, run):
    """
    Build FULL trial-level rows for a single run.
    """

    rows = []

    for trial in run.trials:
        base = enrich_row({}, exp, run, trial)

        row = build_trial_row(
            trial.path,
            specs=None,  # FULL extraction handled in metrics.py
            base_row=base,
        )

        if row:
            rows.append(row)

    return rows
