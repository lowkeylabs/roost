def build_context(exp, run, trial) -> dict:
    """
    Extract context from Experiment, Run, Trial objects.
    No knowledge of MetricSpec here.
    """

    # ----------------------------
    # Experiment
    # ----------------------------
    exp_ctx = {
        "experiment_name": f"{exp.date}_{exp.time}",
        "experiment": exp.id,
        "case_name": exp.case,
        "experiment_date": exp.date,
        "experiment_time": exp.time,
    }

    # ----------------------------
    # Run
    # ----------------------------
    run_ctx = {
        "run_name": run.name,
        "run": getattr(run, "run_id", None),
        "job_name": getattr(run, "job_id", None),
        "master_seed": getattr(run, "master_seed", None),
    }

    # ----------------------------
    # Trial
    # ----------------------------
    trial_ctx = {
        "trial": _safe_int(trial.path.name),
        "trial_status": trial.status,
        "trial_runtime": trial.runtime,
    }

    return {**exp_ctx, **run_ctx, **trial_ctx}


def enrich_row(row: dict | None, exp, run, trial) -> dict | None:
    """
    Merge context into row safely.
    """
    if row is None:
        return None

    ctx = build_context(exp, run, trial)

    # Only inject keys that don't already exist
    for k, v in ctx.items():
        if k not in row:
            row[k] = v

    return row


def _safe_int(x):
    try:
        return int(x)
    except Exception:
        return None
