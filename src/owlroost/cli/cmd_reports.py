from __future__ import annotations

import shutil
from pathlib import Path

import click
import yaml

from owlroost.domain.services.discovery import discover_experiments

# =========================================================
# Helpers
# =========================================================


def write_metadata(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def copy_template(template_path: Path, target_path: Path):
    if not template_path.exists():
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, target_path)


def ensure_report_artifacts(
    target_dir: Path,
    level: str,
    templates_root: Path,
    meta_vars: dict,
):
    target_dir = target_dir.resolve()

    metadata = {
        "level": level,
        "paths": {
            **{k: str(Path(v).resolve()) for k, v in meta_vars.items()},
            "template_dir": str(templates_root.resolve()),
        },
    }

    metadata_path = target_dir / "_metadata.yml"
    write_metadata(metadata_path, metadata)

    template_qmd = templates_root / level / f"{level}.qmd"
    target_qmd = target_dir / f"{level}.qmd"

    copy_template(template_qmd, target_qmd)


def check_report_artifacts(target_dir: Path, level: str):
    issues = []

    if not (target_dir / "_metadata.yml").exists():
        issues.append("missing _metadata.yml")

    if not (target_dir / f"{level}.qmd").exists():
        issues.append(f"missing {level}.qmd")

    return issues


# =========================================================
# CLI Command
# =========================================================


@click.command("reports")
@click.option(
    "--init",
    "init_src",
    type=click.Path(path_type=Path),
    help="Initialize templates from source folder.",
)
@click.option(
    "--sync",
    is_flag=True,
    help="Sync reporting artifacts.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing ./templates folder (used with --init).",
)
@click.option(
    "--results-dir",
    type=click.Path(path_type=Path),
    default=Path("./results"),
)
@click.option(
    "--templates-dir",
    type=click.Path(path_type=Path),
    default=Path("./templates"),
)
def cmd_reports(init_src, sync, force, results_dir: Path, templates_dir: Path):
    """
    Manage reporting layer.

    Modes:
      --init <path> : initialize templates from source
      --sync        : generate metadata + qmd files
      (none)        : diagnostics
    """

    results_dir = results_dir.resolve()
    templates_dir = templates_dir.resolve()

    # =====================================================
    # INIT
    # =====================================================
    if init_src is not None:
        src = init_src.resolve()
        dst = Path.cwd() / "templates"
        project_root = Path.cwd()

        if not src.exists():
            raise click.ClickException(f"Source templates not found: {src}")

        if not src.is_dir():
            raise click.ClickException(f"Source must be a directory: {src}")

        # ---- Safety check for expected structure ----
        required = ["case", "experiment", "run", "trial"]
        missing = [d for d in required if not (src / d).exists()]

        if missing:
            click.echo(
                f"Warning: source templates missing subfolders: {', '.join(missing)}",
                err=True,
            )

        # ---- Copy templates folder ----
        if dst.exists():
            if not force:
                raise click.ClickException(
                    "Destination ./templates already exists. Use --force to overwrite."
                )
            shutil.rmtree(dst)

        shutil.copytree(src, dst)

        # ---- Promote project-level files ----
        promote_files = ["_quarto.yml", "_variables.yml"]

        for fname in promote_files:
            src_file = dst / fname
            dst_file = project_root / fname

            if not src_file.exists():
                click.echo(f"Warning: {fname} not found in templates", err=True)
                continue

            if dst_file.exists():
                if not force:
                    click.echo(
                        f"Warning: {fname} already exists at project root (skipping)",
                        err=True,
                    )
                    continue
                dst_file.unlink()

            shutil.move(str(src_file), str(dst_file))
            click.echo(f"Moved {fname} → project root")

        click.echo(f"Templates initialized from: {src}")
        click.echo(f"Templates directory: {dst}")

        return

    # =====================================================
    # SYNC
    # =====================================================
    if sync:
        if not results_dir.exists():
            raise click.ClickException(f"Results directory not found: {results_dir}")

        if not templates_dir.exists():
            raise click.ClickException(f"Templates directory not found: {templates_dir}")

        experiments = discover_experiments(results_dir)
        case_seen = set()

        for exp in experiments:
            exp_dir = Path(exp.path).resolve()
            case_dir = exp_dir.parent.parent

            # CASE
            if case_dir not in case_seen:
                ensure_report_artifacts(
                    case_dir,
                    "case",
                    templates_dir,
                    {"case_dir": case_dir},
                )
                case_seen.add(case_dir)

            # EXPERIMENT
            ensure_report_artifacts(
                exp_dir,
                "experiment",
                templates_dir,
                {
                    "experiment_dir": exp_dir,
                    "case_dir": case_dir,
                },
            )

            # RUNS
            for run in exp.runs:
                run_dir = Path(run.path).resolve()

                ensure_report_artifacts(
                    run_dir,
                    "run",
                    templates_dir,
                    {
                        "run_dir": run_dir,
                        "experiment_dir": exp_dir,
                        "case_dir": case_dir,
                    },
                )

                if 0:
                    # TRIALS
                    for trial in run.trials:
                        trial_dir = Path(trial.path).resolve()

                        ensure_report_artifacts(
                            trial_dir,
                            "trial",
                            templates_dir,
                            {
                                "trial_dir": trial_dir,
                                "run_dir": run_dir,
                                "experiment_dir": exp_dir,
                                "case_dir": case_dir,
                            },
                        )

                else:
                    # TRIALS (only first trial, e.g., 0000)
                    if run.trials:
                        # Sort to ensure deterministic "first"
                        first_trial = sorted(run.trials, key=lambda t: Path(t.path).name)[0]

                        trial_dir = Path(first_trial.path).resolve()

                        ensure_report_artifacts(
                            trial_dir,
                            "trial",
                            templates_dir,
                            {
                                "trial_dir": trial_dir,
                                "run_dir": run_dir,
                                "experiment_dir": exp_dir,
                                "case_dir": case_dir,
                            },
                        )

        click.echo("Report sync complete.")
        return

    # =====================================================
    # DIAGNOSTICS
    # =====================================================
    if not results_dir.exists():
        raise click.ClickException(f"Results directory not found: {results_dir}")

    experiments = discover_experiments(results_dir)

    template_required = ["case", "experiment", "run", "trial"]

    template_status = {
        "exists": templates_dir.exists(),
        "missing_subdirs": [],
    }

    if template_status["exists"]:
        for sub in template_required:
            if not (templates_dir / sub).exists():
                template_status["missing_subdirs"].append(sub)

    counts = {
        "case": {"total": 0, "missing": 0},
        "experiment": {"total": 0, "missing": 0},
        "run": {"total": 0, "missing": 0},
        "trial": {"total": 0, "missing": 0},
    }

    def check_and_count(path: Path, level: str):
        issues = check_report_artifacts(path, level)
        counts[level]["total"] += 1
        if issues:
            counts[level]["missing"] += 1

    case_seen = set()

    for exp in experiments:
        exp_dir = Path(exp.path).resolve()
        case_dir = exp_dir.parent.parent

        if case_dir not in case_seen:
            check_and_count(case_dir, "case")
            case_seen.add(case_dir)

        check_and_count(exp_dir, "experiment")

        for run in exp.runs:
            run_dir = Path(run.path).resolve()
            check_and_count(run_dir, "run")

            if 0:
                for trial in run.trials:
                    trial_dir = Path(trial.path).resolve()
                    check_and_count(trial_dir, "trial")

            else:
                # Only check first trial per run
                if run.trials:
                    first_trial = sorted(run.trials, key=lambda t: Path(t.path).name)[0]
                    trial_dir = Path(first_trial.path).resolve()
                    check_and_count(trial_dir, "trial")

    click.echo("Reporting Diagnostics\n")

    if not template_status["exists"]:
        click.echo("Templates:   MISSING (./templates not found)")
    elif template_status["missing_subdirs"]:
        missing = ", ".join(template_status["missing_subdirs"])
        click.echo(f"Templates:   INCOMPLETE (missing: {missing})")
    else:
        click.echo("Templates:   OK")

    click.echo()

    def line(label, key):
        c = counts[key]
        click.echo(f"{label:<12} {c['total']:>6} (missing: {c['missing']})")

    line("Cases:", "case")
    line("Experiments:", "experiment")
    line("Runs:", "run")
    line("Trials:", "trial")

    click.echo()

    total_missing = sum(v["missing"] for v in counts.values())
    template_problem = not template_status["exists"] or len(template_status["missing_subdirs"]) > 0

    if total_missing == 0 and not template_problem:
        click.echo("✔ Reporting system is fully in sync.")
    else:
        click.echo("⚠ Reporting system is NOT in sync.")
