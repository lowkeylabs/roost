# src/owlroost/cli/progress_ui.py

from tqdm import tqdm
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)

def create_progress(console=None, description="Working"):
    """
    Standard progress bar factory for all CLI commands.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn(f"[bold blue]{description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    )
    


class TqdmProgressRenderer(BaseProgressRenderer):
    def __init__(self, desc="Total Progress"):
        self.desc = desc
        self.pbar = None

    def start(self, total: int):
        self.pbar = tqdm(
            total=total,
            desc=self.desc,
            unit="trial",
            dynamic_ncols=True,
            smoothing=0.1,
        )

    def advance(self, delta: int, current: int, total: int):
        if delta > 0:
            self.pbar.update(delta)

        elapsed = self.pbar.format_dict.get("elapsed", 0) or 0
        rate = current / elapsed if elapsed > 0 else 0
        self.pbar.set_postfix_str(f"{current}/{total} | {rate:.1f} t/s")

    def finish(self):
        if self.pbar:
            self.pbar.set_postfix_str("complete")
            self.pbar.close()

class RichProgressRenderer(BaseProgressRenderer):
    def __init__(self, console=None, desc="Working"):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]{desc}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        )
        self.task = None

    def start(self, total: int):
        self.progress.start()
        self.task = self.progress.add_task("task", total=total)

    def advance(self, delta: int, current: int, total: int):
        if delta > 0:
            self.progress.advance(self.task, delta)

    def finish(self):
        self.progress.stop()

        