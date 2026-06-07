# src/owlroost/core/progress.py
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
    elapsed: float | None = None,
    started_at: float | None = None,
    finished_at: float | None = None,
):
    """
    Append a progress record.

    Format:
    finished_at,job_id,trial_id,status,elapsed,started_at

    Notes:
    - finished_at is the primary timestamp (used for ordering)
    - elapsed is wall-clock duration of the trial
    - started_at enables queue-delay and concurrency analysis
    """

    # Prefer true finish time from worker; fallback to now
    ts = finished_at if finished_at is not None else time.time()

    # Normalize values
    elapsed_val = float(elapsed) if elapsed is not None else 0.0
    started_val = float(started_at) if started_at is not None else 0.0

    line = f"{ts:.6f},{job_id},{trial_id},{status},{elapsed_val:.6f},{started_val:.6f}\n"

    # Append safely
    with open(progress_file, "a") as f:
        f.write(line)
        f.flush()


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

    seen_completed = set()
    file_pos = 0
    file_handle = None

    try:
        renderer.start(total)
        renderer._last = 0  # initialize renderer state

        while True:
            if stop_event is not None and stop_event.is_set():
                break

            # -----------------------------------------
            # Open file once (tail pattern)
            # -----------------------------------------
            if progress_file.exists():
                if file_handle is None:
                    file_handle = open(progress_file)

                file_handle.seek(file_pos)

                for line in file_handle:
                    parts = line.strip().split(",")

                    if len(parts) < 4:
                        continue

                    _, job_id, trial_id, status, *_ = parts

                    if status in ("completed", "failed", "timeout"):
                        seen_completed.add((job_id, trial_id))

                file_pos = file_handle.tell()

            # -----------------------------------------
            # Compute progress safely
            # -----------------------------------------
            current = min(len(seen_completed), total)
            delta = current - renderer._last

            if delta > 0:
                renderer.advance(delta, current, total)
                renderer._last = current

            # -----------------------------------------
            # Completion condition
            # -----------------------------------------
            if current >= total:
                break

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        pass
    finally:
        if file_handle:
            file_handle.close()
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
