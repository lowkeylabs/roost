# src/owlroost/core/progress.py
import os
import time
from pathlib import Path

from omegaconf import OmegaConf


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
    renderer=None,
):
    if renderer is None:
        raise ValueError("monitor_progress requires a renderer")

    last_val = 0

    try:
        renderer.start(total)

        while True:
            if stop_event is not None and stop_event.is_set():
                break

            val = read_progress(progress_file)

            if val >= total:
                renderer.advance(val - last_val, val, total)
                break

            delta = val - last_val
            if delta > 0:
                renderer.advance(delta, val, total)
                last_val = val

            time.sleep(poll_interval)

        # final flush
        final_val = read_progress(progress_file)
        if final_val > last_val:
            renderer.advance(final_val - last_val, final_val, total)

    except KeyboardInterrupt:
        pass
    finally:
        renderer.finish()


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
