# src/owlroost/core/progress.py
import os
import time
from pathlib import Path

from omegaconf import OmegaConf
from tqdm import tqdm


# --------------------------------------------------
# File lifecycle
# --------------------------------------------------
def init_progress(progress_file: Path):
    """
    Ensure progress file exists.
    Safe for concurrent calls.
    """
    if not progress_file.exists():
        progress_file.write_text("")


# --------------------------------------------------
# Recording progress
# --------------------------------------------------


def record_progress(
    progress_file: Path,
    job_id: str,
    trial_id: int,
    status: str,
    duration: float | None = None,
):
    ts = time.time()

    line = f"{ts},{job_id},{trial_id},{status},{duration or 0:.3f}\n"

    with open(progress_file, "a") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


# --------------------------------------------------
# Reading progress
# --------------------------------------------------
def read_progress(progress_file: Path) -> int:
    """
    Count completed units.
    """
    try:
        with open(progress_file) as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0


# --------------------------------------------------
# Monitor (tqdm)
# --------------------------------------------------
def monitor_progress(
    progress_file: Path,
    total: int,
    stop_event=None,
    poll_interval: float = 0.2,
):
    last_val = 0

    try:
        with tqdm(
            total=total,
            desc="Total Progress",
            unit="trial",
            dynamic_ncols=True,
            smoothing=0.1,
        ) as pbar:
            while True:
                # -----------------------------------------
                # Optional stop signal (safe if None)
                # -----------------------------------------
                if stop_event is not None and stop_event.is_set():
                    break

                val = read_progress(progress_file)

                # -----------------------------------------
                # Completion condition
                # -----------------------------------------
                if val >= total:
                    pbar.update(val - pbar.n)
                    break

                # -----------------------------------------
                # Incremental update
                # -----------------------------------------
                delta = val - last_val
                if delta > 0:
                    pbar.update(delta)
                    last_val = val

                # -----------------------------------------
                # Throughput display
                # -----------------------------------------
                elapsed = pbar.format_dict.get("elapsed", 0) or 0
                rate = val / elapsed if elapsed > 0 else 0

                pbar.set_postfix_str(f"{val}/{total} | {rate:.1f} t/s")

                time.sleep(poll_interval)

            # -----------------------------------------
            # Final flush (guarantee 100%)
            # -----------------------------------------
            final_val = read_progress(progress_file)
            if final_val > pbar.n:
                pbar.update(final_val - pbar.n)

            # Force clean final state display
            pbar.set_postfix_str(f"{total}/{total} | complete")

    except KeyboardInterrupt:
        pass


def get_total_runs_from_overrides(raw_overrides: list[str]) -> int:
    total = 1

    for o in raw_overrides:
        if "=" not in o:
            continue

        key, val = o.split("=", 1)
        val = val.strip()

        # Skip bracket lists
        if val.startswith("[") and val.endswith("]"):
            continue

        # Skip quoted strings
        if (val.startswith('"') and val.endswith('"')) or (
            val.startswith("'") and val.endswith("'")
        ):
            continue

        if "," in val:
            parts = [p.strip() for p in val.split(",") if p.strip()]
            if len(parts) > 1:
                total *= len(parts)

    return total


def get_total_runs_from_multirun(run_dir: Path) -> int:
    """
    Load multirun.yaml from sweep root and compute total runs.
    """
    multirun_file = run_dir.parent / "multirun.yaml"

    if not multirun_file.exists():
        return 1

    cfg_multi = OmegaConf.load(multirun_file)

    task_overrides = cfg_multi.hydra.overrides.task

    return get_total_runs_from_overrides(task_overrides)
