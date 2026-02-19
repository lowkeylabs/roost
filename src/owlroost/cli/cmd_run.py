# src/owlroost/cli/cmd_run.py

import subprocess
import sys
import time
import tomllib
from pathlib import Path

import click
from loguru import logger
from owlplanner.rate_models.loader import _collect_all_model_metadata

from owlroost.cli.utils import (
    find_case_files,
    format_click_options,
    format_override_help,
    index_case_files,
    print_case_list,
    resolve_case_selector,
)

CONF_DIR = Path(__file__).parents[1] / "conf"

helper_groups = [
    "basic_info",
    "savings_assets",
    "fixed_income",
    "rates",
    "asset_allocation",
    "optimization",
    "solver",
]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def format_elapsed(seconds: float) -> str:
    if seconds < 120:
        return f"{seconds:.1f}s"

    total_seconds = int(round(seconds))
    minutes, sec = divmod(total_seconds, 60)

    if minutes < 60:
        return f"{minutes:d}:{sec:02d}"

    hours, minutes = divmod(minutes, 60)
    return f"{hours:d}:{minutes:02d}:{sec:02d}"


def get_rate_selection_method(case_file: Path) -> str | None:
    try:
        with case_file.open("rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise click.ClickException(f"Failed to read case file {case_file}: {e}") from None

    return data.get("rates_selection", {}).get("method")


# ---------------------------------------------------------------------
# Stochastic Detection
# ---------------------------------------------------------------------


def effective_rate_method(case_method: str | None, overrides: list[str]) -> str | None:
    """
    Determine effective rate method considering Hydra overrides.

    Supports:
      - rates_selection=<model>            (Hydra group override)
      - rates_selection.method=<model>     (direct field override)
    """

    for o in overrides:
        if o.startswith("rates_selection="):
            return o.split("=", 1)[1]

        if o.startswith("rates_selection.method="):
            return o.split("=", 1)[1]

    return case_method


def is_stochastic_execution(rate_method: str | None, overrides: list[str]) -> bool:
    """
    Return True if any stochastic dimension is active:
      - Stochastic rate model (via metadata)
      - Longevity model override (Hydra group)
    """

    # ------------------------------------------------------------
    # 1️⃣ Longevity group override
    # ------------------------------------------------------------
    for o in overrides:
        if o.startswith("longevity="):
            # For now any explicit longevity model enables stochastic dimension.
            return True

    # ------------------------------------------------------------
    # 2️⃣ Rate model metadata
    # ------------------------------------------------------------
    if rate_method is None:
        return False

    model_lookup = {entry["method"]: entry for entry in _collect_all_model_metadata()}

    entry = model_lookup.get(rate_method)

    if entry is None:
        return False

    # deterministic=True → NOT stochastic
    return not entry.get("deterministic", True)


def validate_rate_method_for_trials(
    *,
    rate_method: str | None,
    overrides: list[str],
    trials: int | None,
    trial_id: int | None,
):
    """
    Multi-trial execution requires at least one stochastic dimension.
    """

    requires_trials = (trials is not None and trials > 1) or (
        trial_id is not None and trial_id != 0
    )

    if not requires_trials:
        return

    if not is_stochastic_execution(
        rate_method=rate_method,
        overrides=overrides,
    ):
        raise click.ClickException(
            "Invalid configuration for trial execution.\n\n"
            "Multiple trials require at least one stochastic model.\n"
            "Enable a stochastic rate model or use the longevity model override.\n"
        )


# ---------------------------------------------------------------------
# Hydra command builder
# ---------------------------------------------------------------------


def build_hydra_command(
    case_file: Path | None,
    overrides: list[str],
    *,
    trials: int | None,
    trial_jobs: int | None,
    run_jobs: int | None,
    trial_id: int | None,
) -> list[str]:
    package_root = Path(__file__).parents[1]
    script = package_root / "hydra" / "owl_hydra_run.py"
    conf_dir = package_root / "conf"

    if not script.exists():
        raise RuntimeError(f"Hydra runner not found: {script}") from None

    if not conf_dir.exists():
        raise RuntimeError(f"Hydra conf directory not found: {conf_dir}") from None

    cmd = [
        sys.executable,
        str(script),
        "--multirun",
        f"--config-path={conf_dir}",
        "--config-name=config",
    ]

    if case_file:
        cmd.append(f"case.file={case_file}")

    if trials is not None:
        cmd.append(f"trial.count={trials}")

    if trial_jobs is not None:
        cmd.append(f"trial.n_jobs={trial_jobs}")

    if trial_id is not None:
        cmd.append(f"trial.id={trial_id}")

    if run_jobs is not None:
        cmd.append(f"launcher.n_jobs={run_jobs}")

    cmd.extend(overrides)

    return cmd


# ---------------------------------------------------------------------
# CLI Help
# ---------------------------------------------------------------------


def build_run_help(cmd) -> str:
    conf_dir = Path(__file__).parents[1] / "conf"

    parts = [
        "Usage: roost run [CASE] [OPTIONS] [OVERRIDES...]\n",
        "Run OWL via Hydra.\n",
        "",
        "Parallelism:",
        "  -t, --trials INTEGER          Number of stochastic trials (trial.count)",
        "      --trial-id INTEGER        Run a specific trial id (trial.id)",
        "      --trial-jobs INTEGER      Max concurrent trials per run (trial.n_jobs)",
        "      --run-jobs INTEGER        Max concurrent Hydra runs (launcher.n_jobs)",
        "",
        "Examples:",
        "  roost run Case.toml",
        "  roost run Case.toml -t 100",
        "  roost run Case.toml --trial-id 7",
        "  roost run Case.toml -t 100 --trial-id 7",
        "  roost run Case.toml -t 100 --trial-jobs 8 --run-jobs 4",
        "",
        format_override_help(conf_dir, groups=helper_groups),
        format_click_options(cmd),
    ]

    return "\n".join(parts)


# ---------------------------------------------------------------------
# CLI Command
# ---------------------------------------------------------------------


@click.command(
    name="run",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("case", required=False)
@click.option("-t", "--trials", type=int, default=None)
@click.option("--trial-id", type=int, default=None)
@click.option("--trial-jobs", type=int, default=None)
@click.option("--run-jobs", type=int, default=None)
@click.pass_context
def cmd_run(
    ctx: click.Context,
    case: str | None,
    trials: int | None,
    trial_id: int | None,
    trial_jobs: int | None,
    run_jobs: int | None,
):
    cwd = Path.cwd()
    files = find_case_files(cwd)

    if case is None:
        print_case_list(cwd)
        return

    if not files:
        raise click.BadParameter("No .toml case files found.")

    indexed_files = index_case_files(files)
    case_file = resolve_case_selector(case, indexed_files)

    if not case_file:
        raise click.BadParameter(f"No case matching '{case}'")

    rate_method = get_rate_selection_method(case_file)
    hydra_overrides = ctx.args

    effective_method = effective_rate_method(rate_method, hydra_overrides)

    validate_rate_method_for_trials(
        rate_method=effective_method,
        overrides=hydra_overrides,
        trials=trials,
        trial_id=trial_id,
    )

    logger.debug("Resolved case file: {}", case_file)
    logger.debug("Hydra overrides: {}", hydra_overrides)

    cmd = build_hydra_command(
        case_file,
        hydra_overrides,
        trials=trials,
        trial_jobs=trial_jobs,
        run_jobs=run_jobs,
        trial_id=trial_id,
    )

    logger.debug("Executing Hydra:")
    logger.debug("  {}", " ".join(cmd))

    start = time.perf_counter()

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        elapsed = time.perf_counter() - start
        logger.info("Hydra failed after {}", format_elapsed(elapsed))
        raise click.ClickException(f"Hydra run failed (exit {e.returncode})") from None
    else:
        elapsed = time.perf_counter() - start
        logger.info(
            "Hydra completed successfully in {}",
            format_elapsed(elapsed),
        )


cmd_run.get_help = lambda ctx: build_run_help(cmd_run)
