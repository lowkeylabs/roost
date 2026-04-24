# /src/owlroost/domain/services/results_pruning.py

import shutil
from pathlib import Path


def prune_empty_experiments(results_dir: Path, console=None):
    """
    Remove empty time and date folders after purge.

    A time folder is removed if it contains no run_* directories.
    A date folder is removed if it contains no time folders.
    """

    for case_dir in sorted(p for p in results_dir.iterdir() if p.is_dir()):
        for date_dir in sorted(p for p in case_dir.iterdir() if p.is_dir()):
            # Track if any time dirs remain
            remaining_time_dirs = []

            for time_dir in sorted(p for p in date_dir.iterdir() if p.is_dir()):
                # Does this time_dir contain any run_* folders?
                has_runs = any(p.is_dir() and p.name.startswith("run_") for p in time_dir.iterdir())

                if not has_runs:
                    # Remove entire time_dir
                    shutil.rmtree(time_dir)

                    if console:
                        console.print(f"[dim]Pruned empty experiment:[/dim] {time_dir}")
                else:
                    remaining_time_dirs.append(time_dir)

            # If no time dirs remain → remove date_dir
            if not any(p.is_dir() for p in date_dir.iterdir()):
                shutil.rmtree(date_dir)

                if console:
                    console.print(f"[dim]Pruned empty date:[/dim] {date_dir}")

        # Optional: prune empty case_dir (probably rare, but safe)
        if not any(p.is_dir() for p in case_dir.iterdir()):
            shutil.rmtree(case_dir)

            if console:
                console.print(f"[dim]Pruned empty case:[/dim] {case_dir}")
