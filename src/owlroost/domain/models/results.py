# src/owlroost/domain/models/audit.py

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


@dataclass
class Experiment:
    id: int
    case: str
    date: str
    time: str
    path: Path
    runs: list[Run]
