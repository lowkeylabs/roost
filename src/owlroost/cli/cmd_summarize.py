from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

import click
import pandas as pd
import yaml
from loguru import logger

from owlroost.cli.cmd_results import (
    RESULTS_DIR,
    discover_cases,
    extract_run_overrides,
    resolve_case,
)

# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------


@click.command(name="summarize")
@click.argument("case", required=False)
@click.option("--overwrite", is_flag=True)
@click.option("--open", "open_after", is_flag=True)
def cmd_summarize(case, overwrite, open_after):
    """
    Generate experiment_results.xlsx for experiments.

    If CASE provided → summarize experiments for that case.
    If no CASE → summarize all experiments missing XLSX.
    """

    if not RESULTS_DIR.exists():
        raise click.ClickException("No results directory found.")

    cases = discover_cases(RESULTS_DIR)

    if not cases:
        raise click.ClickException("No results found.")

    if case:
        cases = [resolve_case(case, cases)]

    experiment_index = 0
    experiment_registry = []

    for c in cases:
        for exp in c.experiments:
            if not exp.runs:
                continue

            exp_root = exp.runs[0].path.parent
            output_file = exp_root / "experiment_results.xlsx"

            experiment_registry.append((experiment_index, c.name, exp_root))

            if not output_file.exists() or overwrite:
                logger.info(f"Generating summary for {exp_root}")
                df = build_experiment_dataframe(c.name, exp_root)
                df.to_excel(output_file, index=False)
                logger.info(f"Wrote {output_file}")

                if open_after:
                    try:
                        import subprocess

                        subprocess.run(["xdg-open", str(output_file)], check=False)
                    except Exception:
                        pass
            else:
                logger.debug(f"Skipping existing {output_file}")

            experiment_index += 1

    # ------------------------------------------------------------
    # Print experiment registry
    # ------------------------------------------------------------
    click.echo("")
    click.echo("EXPERIMENTS")
    click.echo("-" * 100)
    click.echo(f"{'ID':>4}  {'Case':<20}  {'Path'}")
    click.echo("-" * 100)

    for eid, cname, path in experiment_registry:
        click.echo(f"{eid:>4}  {cname:<20}  {path}")

    click.echo("")
    click.echo("Done.")


# ------------------------------------------------------------
# Core Dataframe Builder
# ------------------------------------------------------------


def build_experiment_dataframe(case_name: str, experiment_path: Path) -> pd.DataFrame:
    rows = []

    experiment_date = experiment_path.parent.name
    experiment_time = experiment_path.name

    # ---------------------------------------------------------
    # Extract experiment + case.file from multirun.yaml
    # ---------------------------------------------------------

    multirun_yaml = experiment_path / "multirun.yaml"
    experiment_name = None
    case_file_path = None

    if multirun_yaml.exists():
        data = yaml.safe_load(multirun_yaml.read_text()) or {}

        task_overrides = data.get("hydra", {}).get("overrides", {}).get("task", [])

        for o in task_overrides:
            if not isinstance(o, str):
                continue

            if o.startswith("case.file="):
                case_file_path = o.split("=", 1)[1]

            elif o.startswith("roost.experiment="):
                experiment_name = o.split("=", 1)[1]

    case_file_name = Path(case_file_path).name if case_file_path else None

    # ---------------------------------------------------------
    # Process runs
    # ---------------------------------------------------------

    run_dirs = sorted(
        p for p in experiment_path.iterdir() if p.is_dir() and p.name.startswith("run_")
    )

    for run_id, run_dir in enumerate(run_dirs):
        run_name = run_dir.name
        overrides = extract_run_overrides(run_dir / "hydra_meta.yaml")

        trials_dir = run_dir / "trials"
        if not trials_dir.exists():
            continue

        trial_dirs = sorted(p for p in trials_dir.iterdir())

        run_tag = build_run_tag(overrides)
        run_hash = hashlib.sha1(run_tag.encode()).hexdigest()[:10]

        for trial_dir in trial_dirs:
            trial_id = int(trial_dir.name)

            effective = next(trial_dir.glob("*_effective.toml"), None)
            metrics_file = next(trial_dir.glob("*_metrics.json"), None)

            if not effective or not metrics_file:
                continue

            eff_data = tomllib.loads(effective.read_text())
            metrics = json.loads(metrics_file.read_text())

            row = {}

            # -------------------------------------------------
            # Experiment identity
            # -------------------------------------------------

            row["case_name"] = case_name
            row["case_file"] = case_file_name
            row["experiment"] = experiment_name
            row["experiment_date"] = experiment_date
            row["experiment_time"] = experiment_time
            row["experiment_path"] = str(experiment_path)

            # -------------------------------------------------
            # Run identity
            # -------------------------------------------------

            row["run_name"] = run_name
            row["run_id"] = run_id
            row["trial_id"] = trial_id
            row["run_tag"] = run_tag
            row["run_hash"] = run_hash

            # -------------------------------------------------
            # Reproducibility
            # -------------------------------------------------

            roost = eff_data.get("roost", {})
            row["master_seed"] = roost.get("master_seed")
            row["rates_seed"] = roost.get("rates_seed")
            row["longevity_seed"] = roost.get("longevity_seed")

            # -------------------------------------------------
            # Structured scenario
            # -------------------------------------------------

            rates = eff_data.get("rates_selection", {})
            row["rates_method"] = rates.get("method")
            row["rates_from"] = rates.get("from")
            row["rates_to"] = rates.get("to")
            row["roll_sequence"] = rates.get("roll_sequence")
            row["reverse_sequence"] = rates.get("reverse_sequence")

            # -------------------------------------------------
            # Metrics (prefixed)
            # -------------------------------------------------

            for k, v in metrics.items():
                row[f"metric_{k}"] = v

            # -------------------------------------------------
            # Raw overrides (JSON)
            # -------------------------------------------------

            row["run_overrides"] = json.dumps(overrides)

            rows.append(row)

    return pd.DataFrame(rows)


# ------------------------------------------------------------
# Run Tag Builder
# ------------------------------------------------------------


def build_run_tag(overrides: list[str]) -> str:
    """
    Deterministic human-readable run tag.
    """

    cleaned = sorted(o.replace("\\ ", " ") for o in overrides)

    parts = []

    for o in cleaned:
        if "=" in o:
            k, v = o.split("=", 1)
            parts.append(f"{k.split('.')[-1]}={v}")
        else:
            parts.append(o)

    return "|".join(parts)
