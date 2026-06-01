# src/owlroost/core/progress_renderers.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


# =========================================================
# Base
# =========================================================
class BaseProgressRenderer:
    def start(
        self,
        total: int,
    ):
        raise NotImplementedError

    def advance(
        self,
        delta: int,
        current: int,
        total: int,
    ):
        raise NotImplementedError

    def finish(
        self,
    ):
        raise NotImplementedError


# =========================================================
# Null renderer
# =========================================================
class NullProgressRenderer(BaseProgressRenderer):
    def start(
        self,
        total: int,
    ):
        pass

    def advance(
        self,
        delta: int,
        current: int,
        total: int,
    ):
        pass

    def finish(
        self,
    ):
        pass


# =========================================================
# Dot renderer
# =========================================================
class DotProgressRenderer(BaseProgressRenderer):
    def __init__(
        self,
        stream=None,
    ):
        import sys

        self.stream = stream or sys.stdout

    def start(
        self,
        total: int,
    ):
        self.total = total

    def advance(
        self,
        delta: int,
        current: int,
        total: int,
    ):
        if delta > 0:
            self.stream.write("." * delta)

            self.stream.flush()

    def finish(
        self,
    ):
        self.stream.write("\n")
        self.stream.flush()


# =========================================================
# Dot2 renderer
# =========================================================
class Dot2ProgressRenderer(BaseProgressRenderer):
    def __init__(
        self,
        stream=None,
    ):
        import sys

        self.stream = stream or sys.stdout

    def start(
        self,
        total: int,
    ):
        self.total = total

    def advance(
        self,
        delta: int,
        current: int,
        total: int,
    ):
        if delta > 0:
            self.stream.write("." * delta)

            if current % 50 == 0:
                self.stream.write(f" {current}/{total}\n")

            self.stream.flush()

    def finish(
        self,
    ):
        self.stream.write("\n")
        self.stream.flush()


# =========================================================
# Rich renderer
# =========================================================
class RichProgressRenderer(BaseProgressRenderer):
    def __init__(
        self,
        console=None,
        desc: str = "Working",
    ):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]{desc}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TextColumn(
                "[dim]{task.fields[speed]}",
                justify="right",
            ),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        )

        self.task = None

    def start(
        self,
        total: int,
    ):
        self.progress.start()

        self.task = self.progress.add_task(
            "task",
            total=total,
            speed="",
        )

    def advance(
        self,
        delta: int,
        current: int,
        total: int,
    ):
        if delta <= 0:
            return

        task = self.progress.tasks[self.task]

        elapsed = task.elapsed or 0

        rate = current / elapsed if elapsed and elapsed > 0.25 else 0

        self.progress.update(
            self.task,
            advance=delta,
            speed=(f"{rate:.1f}/s" if rate > 0 else ""),
        )

    def finish(
        self,
    ):
        self.progress.stop()


# =========================================================
# Factory
# =========================================================
def create_renderer(
    kind: str,
    console=None,
    desc: str = "Working",
):
    kind = (kind or "rich").lower()

    if kind == "rich":
        try:
            return RichProgressRenderer(
                console,
                desc,
            )

        except Exception:
            return Dot2ProgressRenderer()

    if kind == "dot":
        return DotProgressRenderer()

    if kind == "dot2":
        return Dot2ProgressRenderer()

    if kind == "none":
        return NullProgressRenderer()

    raise ValueError(f"Unknown renderer: {kind}")
