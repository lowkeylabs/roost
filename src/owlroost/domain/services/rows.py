from __future__ import annotations

from owlroost.domain.metrics.metric_registry import METRIC_REGISTRY
from owlroost.domain.services.aggregation import aggregate_rows
from owlroost.domain.services.context import enrich_row
from owlroost.domain.services.metrics import build_trial_row

# =========================================================
# RUN ROWS
# =========================================================


def _invariant_value(trial_rows, key_path):
    values = []

    for r in trial_rows:
        val = r
        for k in key_path:
            val = (val or {}).get(k)
        if val is not None:
            values.append(val)

    if not values:
        return None

    first = values[0]

    if not all(v == first for v in values):
        return "MIXED"

    return first


def build_run_rows(experiments):
    """
    Build aggregated run-level rows across all experiments.

    Each row represents a run (aggregated from its trials).
    """

    run_rows = []

    for exp_index, exp in enumerate(experiments):
        all_trials = build_trial_rows([exp])

        for run_index, _run in enumerate(exp.runs):
            trial_rows = [r for r in all_trials if r.get("run") == run_index]
            if not trial_rows:
                continue

            summary = aggregate_rows(trial_rows)

            summary["worker_timeout"] = _invariant_value(
                trial_rows,
                ["_inputs", "roost", "worker_timeout"],
            )

            trial_summaries = [
                {
                    "trial_id": r.get("trial_id"),
                    "status": r.get("status"),
                    "failure_category": r.get("failure_category"),
                    "failure_subtype": r.get("failure_subtype"),
                    "_inputs": r.get("_inputs"),  # 🔥 REQUIRED
                }
                for r in trial_rows
            ]

            summary["trial_summaries"] = trial_summaries

            # -------------------------------------------------
            # Carry forward non-aggregated fields (robust)
            # -------------------------------------------------
            for k in trial_rows[0].keys():
                if k in summary:
                    continue

                vals = [r.get(k) for r in trial_rows if r.get(k) not in (None, {}, [])]

                if not vals:
                    continue

                # If all meaningful values are identical → keep it
                first = vals[0]
                if all(v == first for v in vals):
                    summary[k] = first

            # ==================================================
            # RUN-LEVEL DERIVED METRICS
            # ==================================================

            for key, spec in METRIC_REGISTRY.items():
                if not spec.compute_fn:
                    continue

                if spec.compute_level != "run":
                    continue

                try:
                    summary[key] = spec.compute_fn(summary)
                except Exception:
                    summary[key] = None

            summary["_ref"] = {
                "exp_index": exp_index,
                "run_index": run_index,
            }

            run_rows.append(summary)

    return run_rows


# =========================================================
# TRIAL ROWS
# =========================================================


def build_trial_rows(experiments):
    rows = []

    for exp in experiments:
        for run in exp.runs:
            for trial in run.trials:
                base = enrich_row({}, exp, run, trial)
                # base["run"] = run_index
                # base["run_name"] = run.name

                data = trial.data or {}

                status = (data.get("status") or trial.status or "").upper()

                failure_category = data.get("failure_category")
                if status == "FAILED" and not failure_category:
                    failure_category = "unknown_failure"

                base.update(
                    {
                        "trial_id": trial.path.name,
                        "status": status,
                        "failure_category": failure_category,
                        "failure_detail": data.get("failure_detail"),
                        "runtime": data.get("runtime") or trial.runtime,
                    }
                )

                row = build_trial_row(
                    trial.path,
                    specs=None,
                    base_row=base,
                )

                if row:
                    rows.append(row)

    return rows
