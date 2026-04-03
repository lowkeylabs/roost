def build_context(exp, run, trial) -> dict:
    """
    Extract context from Experiment, Run, Trial objects.
    No knowledge of MetricSpec here.

    Extended to include:
      - experiment-level common overrides
      - run-specific overrides
      - flattened override keys for filtering/pivoting
    """

    # ----------------------------
    # Experiment
    # ----------------------------
    exp_ctx = {
        "experiment_name": f"{exp.date}_{exp.time}",
        "experiment": exp.id,
        "case": getattr(exp, "case_id", None),
        "case_name": exp.case,
        "experiment_date": exp.date,
        "experiment_time": exp.time,
    }

    # Add experiment-level overrides
    exp_overrides = _filter_overrides(getattr(exp, "common_overrides", {}) or {})
    exp_ctx["experiment_overrides"] = exp_overrides

    # Flatten experiment overrides
    exp_ctx.update(_flatten("exp_override", exp_overrides))

    # ----------------------------
    # Run
    # ----------------------------
    run_ctx = {
        "run_name": run.name,
        "run": getattr(run, "run_id", None),
        "job_name": getattr(run, "job_id", None),
        "master_seed": getattr(run, "master_seed", None),
    }

    # Add run-level overrides
    run_common = _filter_overrides(getattr(run, "common_overrides", {}) or {})
    run_specific = getattr(run, "run_overrides", {}) or {}

    run_ctx["common_overrides"] = run_common
    run_ctx["run_specific_overrides"] = run_specific

    # Flatten run-specific overrides (most useful for comparison)
    run_ctx.update(_flatten("run_override", run_specific))

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


# =========================================================
# Helpers
# =========================================================


def _filter_overrides(d: dict) -> dict:
    """
    Remove non-user-facing or redundant override keys.
    """
    if not d:
        return {}

    EXCLUDE = {
        "case.file",
        "trial.count",
    }

    return {k: v for k, v in d.items() if k not in EXCLUDE}


def _flatten(prefix: str, d: dict) -> dict:
    """
    Flatten a dict into dot-prefixed keys.

    Example:
        {"rates.method": "bootstrap"} →
        {"exp_override.rates.method": "bootstrap"}
    """
    if not d:
        return {}

    return {f"{prefix}.{k}": v for k, v in d.items()}


def _safe_int(x):
    try:
        return int(x)
    except Exception:
        return None
