# src/owlroost/domain/models/results.py

from dataclasses import dataclass, field
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

    # ----------------------------
    # NEW: Hydra + override info
    # ----------------------------
    meta: dict = field(default_factory=dict)

    # Overrides common across all runs in experiment
    common_overrides: dict = field(default_factory=dict)

    # Overrides unique to this run
    run_overrides: dict = field(default_factory=dict)


@dataclass
class Experiment:
    id: int
    case: str
    date: str
    time: str
    path: Path
    runs: list[Run]

    # ----------------------------
    # NEW: shared overrides across runs
    # ----------------------------
    common_overrides: dict = field(default_factory=dict)

    @property
    def experiment_id(self) -> str:
        return f"{self.date}_{self.time}"
