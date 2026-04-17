# src/owlroost/cli/cmd_run.py

import ast
import os
import subprocess
import sys
import time
import tomllib
from datetime import datetime
from pathlib import Path
from threading import Thread

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
from owlroost.core.progress import get_total_runs_from_overrides, monitor_progress, read_progress

CONF_DIR = Path(__file__).parents[1] / "conf"

helper_groups = [
    "basic_info",
    "savings_assets",
    "fixed_income",
    "rates_selection",
    "asset_allocation",
    "optimization_parameters",
    "solver_options",
]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
# Experiment Helpers
# ---------------------------------------------------------------------


def parse_from_to_slices(overrides: list[str]) -> list[tuple[int, int]]:
    """
    Extract and parse rates_selection.from_to=[[start,end], ...]
    """
    for o in overrides:
        if o.startswith("rates_selection.from_to="):
            value = o.split("=", 1)[1]
            try:
                slices = ast.literal_eval(value)
            except Exception:
                raise click.ClickException(
                    f"Invalid rates_selection.from_to value: {value}"
                ) from None

            if not isinstance(slices, list):
                raise click.ClickException(
                    "rates_selection.from_to must be a list of [start,end] pairs"
                )

            result = []
            for pair in slices:
                if not isinstance(pair, (list | tuple)) or len(pair) != 2:
                    raise click.ClickException("Each from_to entry must be [start,end]")
                result.append((int(pair[0]), int(pair[1])))

            return result

    raise click.ClickException(
        "augmented_sampling requires rates_selection.from_to=[[start,end],...]"
    )


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


def start_progress_monitor(run_root: Path, total_trials: int):
    # --------------------------------------------------
    # Wait for Hydra to create experiment folder
    # --------------------------------------------------
    run_root.parent.mkdir(parents=True, exist_ok=True)

    deadline = time.time() + 15
    while not run_root.exists():
        if time.time() > deadline:
            raise RuntimeError(f"Timeout waiting for {run_root}")
        time.sleep(0.1)

    progress_file = run_root / "progress.log"

    # --------------------------------------------------
    # Wait for multirun.yaml
    # --------------------------------------------------
    deadline = time.time() + 10
    while not (run_root / "multirun.yaml").exists():
        if time.time() > deadline:
            raise RuntimeError("Timeout waiting for multirun.yaml")
        time.sleep(0.1)

    logger.debug("Multirun yaml detected: {}", run_root / "multirun.yaml")

    # --------------------------------------------------
    # Wait for progress.log
    # --------------------------------------------------
    deadline = time.time() + 10
    while not progress_file.exists():
        if time.time() > deadline:
            raise RuntimeError("Timeout waiting for progress.log")
        time.sleep(0.1)

    # --------------------------------------------------
    # Reset progress file (critical)
    # --------------------------------------------------
    progress_file.write_text("")

    logger.debug("Total trials: {}", total_trials)

    # --------------------------------------------------
    # Start monitor
    # --------------------------------------------------
    monitor_thread = Thread(
        target=monitor_progress,
        args=(progress_file, total_trials, None),
        daemon=False,
    )
    monitor_thread.start()

    return monitor_thread, progress_file


# ---------------------------------------------------------------------
# Hydra command builder
# ---------------------------------------------------------------------


def load_roost_defaults(conf_dir: Path) -> dict:
    path = conf_dir / "roost" / "default.yaml"
    try:
        import yaml

        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def resolve_parallelism(
    *,
    num_runs: int,
    trial_count: int,
    trial_jobs: int | None,
    run_jobs: int | None,
    cfg: dict,
):
    # --------------------------------------------------
    # Config
    # --------------------------------------------------
    max_trial_jobs = cfg.get("max_trial_jobs", 28)
    max_run_jobs = cfg.get("max_run_jobs", 8)
    cpu_reserve = cfg.get("cpu_reserve", 2)
    oversubscribe = cfg.get("oversubscribe_factor", 1.0)

    cpu_count = os.cpu_count() or 1
    base_cpu = max(1, cpu_count - cpu_reserve)
    usable_cpu = max(1, int(base_cpu * oversubscribe))

    # --------------------------------------------------
    # Explicit overrides (handled FIRST)
    # --------------------------------------------------
    if trial_jobs is not None or run_jobs is not None:
        t = trial_jobs if trial_jobs is not None else 1
        r = run_jobs if run_jobs is not None else 1
        return t, r

    # --------------------------------------------------
    # Policy
    # --------------------------------------------------
    if trial_count > 1:
        # parallelize trials
        t = min(max_trial_jobs, trial_count, usable_cpu)
        r = 1
        return t, r

    if num_runs > 1:
        # parallelize runs
        t = 1
        r = min(max_run_jobs, num_runs, usable_cpu)
        return t, r

    # --------------------------------------------------
    # Default (single run, single trial)
    # --------------------------------------------------
    return 1, 1


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
        cmd.append(f"hydra.launcher.n_jobs={run_jobs}")

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
@click.option("--open-folder", is_flag=True, help="Open experiment folder after run.")
@click.pass_context
def cmd_run(
    ctx: click.Context,
    case: str | None,
    trials: int | None,
    trial_id: int | None,
    trial_jobs: int | None,
    run_jobs: int | None,
    open_folder: bool,
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

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")
    results_root = Path.cwd() / "results"

    # extract case name (you already have case_file)
    case_name = case_file.stem.replace("case_", "")

    run_root = results_root / case_name / date_str / time_str

    hydra_overrides = list(ctx.args)
    hydra_overrides = [
        f"hydra.sweep.dir={results_root}/{case_name}/{date_str}/{time_str}",
        *hydra_overrides,
    ]

    num_runs = get_total_runs_from_overrides(hydra_overrides)
    trial_count = trials or 1
    total_trials = num_runs * trial_count

    # ------------------------------------------------------------
    # Auto parallelism policy
    # ------------------------------------------------------------

    cfg = load_roost_defaults(CONF_DIR)

    trial_jobs, run_jobs = resolve_parallelism(
        num_runs=num_runs,
        trial_count=trial_count,
        trial_jobs=trial_jobs,
        run_jobs=run_jobs,
        cfg=cfg,
    )

    # ------------------------------------------------------------
    # Normalize (CRITICAL FIX)
    # ------------------------------------------------------------
    trial_jobs = trial_jobs or 1
    run_jobs = run_jobs or 1

    parallel_jobs = min(run_jobs, num_runs)

    # ------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------
    if cfg.get("enforce_single_axis", True):
        if trial_jobs > 1 and run_jobs > 1:
            raise click.ClickException(
                "Cannot use both trial parallelism and run parallelism simultaneously."
            )

    logger.info(
        "Runs: {} | Parallel runs: {} | Trials: {} | Parallel trials: {}",
        num_runs,
        parallel_jobs,
        total_trials,
        trial_jobs,
    )

    # ------------------------------------------------------------
    # Auto-activate longevity=default if longevity.* override used
    # ------------------------------------------------------------
    if any(o.startswith("longevity.") for o in hydra_overrides):
        if not any(o.startswith("longevity=") for o in hydra_overrides):
            hydra_overrides = ["longevity=default", *hydra_overrides]

    effective_rate_method(rate_method, hydra_overrides)

    logger.debug("Resolved case file: {}", case_file)
    logger.debug("Hydra overrides: {}", hydra_overrides)

    # ------------------------------------------------------------
    # Experiment: augmented_sampling
    # ------------------------------------------------------------

    experiment_name = None
    cleaned = []

    for o in hydra_overrides:
        if o.startswith("experiment="):
            experiment_name = o.split("=", 1)[1]
        else:
            cleaned.append(o)

    base_overrides = cleaned
    if experiment_name:
        base_overrides.append(f"roost.experiment={experiment_name}")

    if experiment_name == "augmented_sampling":
        slices = parse_from_to_slices(hydra_overrides)

        # Remove original from_to override
        base_overrides = [o for o in base_overrides if not o.startswith("rates_selection.from_to=")]

        if not slices:
            raise click.ClickException("augmented_sampling requires at least one from_to slice.")

        # --------------------------------------------------------
        # Determine plan horizon (N_n)
        # --------------------------------------------------------

        try:
            with case_file.open("rb") as f:
                case_data = tomllib.load(f)
        except Exception as e:
            raise click.ClickException(
                f"Failed to read case file for horizon computation: {e}"
            ) from None

        try:
            start_date = case_data["basic_info"]["start_date"]
            life_expectancies = case_data["basic_info"]["life_expectancy"]
            birth_years = [int(d[:4]) for d in case_data["basic_info"]["date_of_birth"]]
        except KeyError as e:
            raise click.ClickException(f"Missing required basic_info field: {e}") from None

        start_year = int(start_date[:4])

        horizon_years = max(
            (birth_year + life - start_year)
            for birth_year, life in zip(
                birth_years,
                life_expectancies,
                strict=False,
            )
        )

        if horizon_years <= 0:
            raise click.ClickException("Computed non-positive planning horizon.")

        # --------------------------------------------------------
        # Build sweep dimensions
        # --------------------------------------------------------

        # Format slice pairs for Hydra sweep
        from_to_values = [f"[{start},{end}]" for start, end in slices]

        # Determine max roll across slices
        roll_values = []

        for start, end in slices:
            S = end - start + 1
            max_roll = min(S, horizon_years)
            for r in range(max_roll):
                roll_values.append(str(r))

        # Remove duplicates but preserve order
        roll_values = list(dict.fromkeys(roll_values))

        sweep_overrides = base_overrides + [
            "rates_selection.method=historical",
            f"rates_selection.from_to={','.join(from_to_values)}",
            f"rates_selection.roll_sequence={','.join(roll_values)}",
            "rates_selection.reverse_sequence=true,false",
        ]

        cmd = build_hydra_command(
            case_file,
            sweep_overrides,
            trials=trials,
            trial_jobs=trial_jobs,
            run_jobs=run_jobs,
            trial_id=trial_id,
        )

        logger.debug("Executing SINGLE Hydra experiment multirun:")
        logger.debug("  {}", " ".join(cmd))

        start_time = time.perf_counter()

        proc = subprocess.Popen(cmd)
        monitor_thread, progress_file = start_progress_monitor(run_root, total_trials)
        proc.wait()

        while read_progress(progress_file) < total_trials:
            time.sleep(0.1)
        monitor_thread.join()

        elapsed = time.perf_counter() - start_time

        logger.info(
            "Experiment 'augmented_sampling' completed in {}",
            format_elapsed(elapsed),
        )

        if open_folder:
            open_latest_results_folder()

        return

    # --------------------------------------------------------
    # default processing outside of experiments
    # --------------------------------------------------------
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

    results_root = Path.cwd() / "results"
    # Start monitor BEFORE Hydra runs
    try:
        proc = subprocess.Popen(cmd)
        monitor_thread, progress_file = start_progress_monitor(run_root, total_trials)
        proc.wait()
        # Wait until progress completes
        while read_progress(progress_file) < total_trials:
            time.sleep(0.1)

        monitor_thread.join()

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

        if open_folder:
            open_latest_results_folder()


def open_latest_results_folder():
    """
    Open the most recent experiment folder under ./results.
    """

    results_dir = Path.cwd() / "results"
    open_in_file_explorer(results_dir)


def _wsl_to_windows_path(path: Path) -> str:
    """Convert a WSL path to a Windows path using wslpath."""
    result = subprocess.run(
        ["wslpath", "-w", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise click.ClickException(f"Failed to convert path for Explorer: {path}")
    return result.stdout.strip()


def open_in_file_explorer(path: Path):
    if not path.exists():
        raise click.ClickException(f"Path does not exist: {path}")

    path = path.resolve()

    # ---- WSL detection ----
    if "microsoft" in os.uname().release.lower():
        win_path = _wsl_to_windows_path(path)
        subprocess.run(["explorer.exe", win_path], check=False)
        return

    # ---- Native Windows ----
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
        return

    # ---- macOS ----
    if sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
        return

    # ---- Native Linux ----
    subprocess.run(["xdg-open", path], check=False)


cmd_run.get_help = lambda ctx: build_run_help(cmd_run)
