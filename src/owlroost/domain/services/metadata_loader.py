from pathlib import Path

import yaml

from owlroost.domain.metrics import load_metrics
from owlroost.domain.services.discovery import discover_experiments


# ---------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------


def _load_metadata(metadata_path: Path):
    with open(metadata_path) as f:
        return yaml.safe_load(f)


def _resolve_results_dir(meta: dict) -> Path:
    results_dir = meta.get("paths", {}).get("results_dir")
    if not results_dir:
        raise ValueError("metadata missing paths.results_dir")
    return Path(results_dir).resolve()


def _build_indexes(experiments):
    """
    Build fast lookup indexes:
        - path_index
        - signature_index
    """
    path_index = {}
    signature_index = {}

    for exp in experiments:
        for run in exp.runs:
            path = Path(run.path).resolve()
            path_index[path] = (exp, run)

            sig = getattr(run, "signature", None)
            if sig is not None:
                signature_index.setdefault(sig, []).append((exp, run))

    return path_index, signature_index


def _resolve_runs(meta: dict, results_dir: Path, experiments):
    """
    Returns list of (exp, run) tuples.

    Now supports:
        - path resolution (existing behavior)
        - signature fallback (self-healing)
    """

    resolved = []

    path_index, signature_index = _build_indexes(experiments)

    # ----------------------------------------
    # Preferred: run_refs (unchanged)
    # ----------------------------------------
    run_refs = meta.get("selection", {}).get("run_refs")

    if run_refs:
        for ref in run_refs:
            exp = experiments[ref["exp_index"]]
            run = exp.runs[ref["run_index"]]
            resolved.append((exp, run))
        return resolved

    # ----------------------------------------
    # Fallback: path-based with self-healing
    # ----------------------------------------
    for r in meta.get("runs", []):
        path_str = r.get("path")
        abs_path_str = r.get("abs_path")
        signature = r.get("signature")

        # ----------------------------------------
        # Resolve target path
        # ----------------------------------------
        if path_str:
            target = (results_dir / path_str).resolve()
        elif abs_path_str:
            target = Path(abs_path_str).resolve()
        else:
            raise ValueError("Invalid run entry: missing path and abs_path")

        # ----------------------------------------
        # 1. Try exact path match
        # ----------------------------------------
        if target in path_index:
            resolved.append(path_index[target])
            continue

        # ----------------------------------------
        # 2. Self-healing via signature
        # ----------------------------------------
        if signature:
            matches = signature_index.get(signature, [])

            if matches:
                # Prefer latest duplicate
                latest = next(
                    ((e, r) for (e, r) in matches if getattr(r, "is_latest_duplicate", False)),
                    None,
                )

                chosen = latest if latest else matches[-1]

                # Optional: debug signal (quiet, but helpful)
                print(
                    f"[metadata_loader] resolved missing run:\n"
                    f"  original: {target}\n"
                    f"  using:    {Path(chosen[1].path)} (latest duplicate)"
                )

                resolved.append(chosen)
                continue

        # ----------------------------------------
        # 3. Hard failure
        # ----------------------------------------
        raise ValueError(f"Run not found and could not be resolved: {target}")

    return resolved


# ---------------------------------------------------------
# Public API
# ---------------------------------------------------------


def load_trial_rows_from_metadata(metadata_path: Path):
    import copy
    from owlroost.domain.services.rows import build_trial_rows

    # ----------------------------------------
    # Load metadata
    # ----------------------------------------
    meta = _load_metadata(metadata_path)
    results_dir = _resolve_results_dir(meta)

    # ----------------------------------------
    # Discover experiments
    # ----------------------------------------
    experiments = discover_experiments(results_dir)

    # ----------------------------------------
    # Resolve runs from metadata
    # ----------------------------------------
    resolved_runs = _resolve_runs(meta, results_dir, experiments)

    if not resolved_runs:
        raise ValueError("No runs resolved from metadata")

    # ----------------------------------------
    # Filter experiments to ONLY those runs
    # ----------------------------------------
    filtered_experiments = []

    for exp in experiments:
        matched_runs = []

        for run in exp.runs:
            for _, resolved_run in resolved_runs:
                if run is resolved_run:
                    matched_runs.append(run)
                    break

        if matched_runs:
            exp_copy = copy.copy(exp)
            exp_copy.runs = matched_runs
            filtered_experiments.append(exp_copy)

    if not filtered_experiments:
        raise ValueError("No matching runs found after filtering")

    # ----------------------------------------
    # Build trial rows EXACTLY like CLI
    # ----------------------------------------
    trial_rows = build_trial_rows(filtered_experiments)

    if not trial_rows:
        raise ValueError("No trial rows produced")

    return trial_rows


def load_final_rows_from_metadata(metadata_path: Path):
    import copy
    from owlroost.domain.services.rows import build_run_rows

    # ----------------------------------------
    # Load metadata
    # ----------------------------------------
    meta = _load_metadata(metadata_path)
    results_dir = _resolve_results_dir(meta)

    # ----------------------------------------
    # Discover experiments
    # ----------------------------------------
    experiments = discover_experiments(results_dir)

    # ----------------------------------------
    # Resolve runs from metadata
    # ----------------------------------------
    resolved_runs = _resolve_runs(meta, results_dir, experiments)

    if not resolved_runs:
        raise ValueError("No runs resolved from metadata")

    # ----------------------------------------
    # Filter experiments to ONLY those runs
    # ----------------------------------------
    filtered_experiments = []

    for exp in experiments:
        matched_runs = []

        for run in exp.runs:
            for _, resolved_run in resolved_runs:
                if run is resolved_run:
                    matched_runs.append(run)
                    break

        if matched_runs:
            exp_copy = copy.copy(exp)
            exp_copy.runs = matched_runs
            filtered_experiments.append(exp_copy)

    if not filtered_experiments:
        raise ValueError("No matching runs found after filtering")

    # ----------------------------------------
    # Build rows EXACTLY like CLI
    # ----------------------------------------
    final_rows = build_run_rows(filtered_experiments)

    if not final_rows:
        raise ValueError("No run rows produced")

    return final_rows


def load_bundle(metadata_path: Path):
    load_metrics()
    meta = _load_metadata(metadata_path)

    final_rows = load_final_rows_from_metadata(metadata_path)
    final_trial_rows = load_trial_rows_from_metadata(metadata_path)

    return {
        "metadata": meta,
        "run_rows": final_rows,
        "trial_rows": final_trial_rows,
    }
