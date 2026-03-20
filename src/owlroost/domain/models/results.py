# src/owlroost/domain/models/results.py

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Trial:
    path: Path
    status: str
    runtime: float | None = None
    data: dict | None = None


@dataclass
class Run:
    name: str
    path: Path
    trials: list[Trial]
    job_id: str | None = None
    run_id: int | None = None
    master_seed: int | None = None


@dataclass
class Experiment:
    id: int
    case: str
    date: str
    time: str
    path: Path
    runs: list[Run]

    @property
    def experiment_id(self) -> str:
        return f"{self.date}_{self.time}"
