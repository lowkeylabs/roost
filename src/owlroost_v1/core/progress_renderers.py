# src/owlroost/core/progress_renderers.py

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)


class BaseProgressRenderer:
    def start(self, total: int):
        raise NotImplementedError

    def advance(self, delta: int, current: int, total: int):
        raise NotImplementedError

    def finish(self):
        raise NotImplementedError


class NullProgressRenderer(BaseProgressRenderer):
    def start(self, total: int):
        pass

    def advance(self, delta: int, current: int, total: int):
        pass

    def finish(self):
        pass


class DotProgressRenderer(BaseProgressRenderer):
    def __init__(self, stream=None):
        import sys

        self.stream = stream or sys.stdout
        self.count = 0

    def start(self, total: int):
        self.total = total

    def advance(self, delta, current, total):
        if delta > 0:
            self.stream.write("." * delta)

    def finish(self):
        self.stream.write("\n")
        self.stream.flush()


class Dot2ProgressRenderer(BaseProgressRenderer):
    def __init__(self, stream=None):
        import sys

        self.stream = stream or sys.stdout
        self.count = 0

    def start(self, total: int):
        self.total = total

    def advance(self, delta, current, total):
        if delta > 0:
            self.stream.write("." * delta)
            if current % 50 == 0:
                self.stream.write(f" {current}/{total}\n")
            self.stream.flush()

    def finish(self):
        self.stream.write("\n")
        self.stream.flush()


class RichProgressRenderer(BaseProgressRenderer):
    def __init__(self, console=None, desc="Working"):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]{desc}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TextColumn("[dim]{task.fields[speed]}", justify="right"),
            TimeElapsedColumn(),
            console=console,
        )
        self.task = None

    def start(self, total: int):
        self.progress.start()
        self.task = self.progress.add_task(
            "task",
            total=total,
            speed="",  # 🔥 FIX: initialize field
        )

    def advance(self, delta, current, total):
        if delta > 0:
            task = self.progress.tasks[self.task]
            elapsed = task.elapsed or 0
            rate = current / elapsed if elapsed > 0 else 0

            self.progress.update(
                self.task,
                advance=delta,
                speed=f"{rate:.1f}/s" if rate > 0 else "",
            )

    def finish(self):
        self.progress.stop()


def create_renderer(kind: str, console=None, desc="Working"):
    kind = (kind or "rich").lower()

    if kind == "rich":
        return RichProgressRenderer(console, desc)

    if kind == "dot":
        return DotProgressRenderer()

    if kind == "none":
        return NullProgressRenderer()

    raise ValueError(f"Unknown renderer: {kind}")
