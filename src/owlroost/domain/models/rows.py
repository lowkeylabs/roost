from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExperimentRow:
    id: int
    case: str
    date: str
    time: str
    runs: int
    trials: int
    solved: int
    failed: int
    incomplete: int
    slow: int
    success_rate: float
    runtime: float | None = None
    spend_basis: float | None = None
    total_spend_real: float | None = None
    bequest_real: float | None = None
    nvars: float | None = None
    ncons: float | None = None
    nnz: float | None = None
    int_ratio: float | None = None


@dataclass
class RunRow:
    experiment_id: int
    case: str
    date: str
    time: str
    run: str

    trials: int
    solved: int
    failed: int
    incomplete: int
    success_rate: float
    slow: int

    # aggregated metrics
    runtime: float | None
    spend_basis: float | None
    total_spend_real: float | None
    bequest_real: float | None

    nvars: float | None
    ncons: float | None
    nnz: float | None
    int_ratio: float | None


@dataclass
class xxRunRow:
    experiment_id: int
    case: str
    date: str
    time: str
    run: str

    trials: int
    solved: int
    failed: int
    incomplete: int
    slow: int
    success_rate: float

    runtime: float | None
    spend_basis: float | None
    total_spend_real: float | None
    bequest_real: float | None

    # optional but powerful
    bequest_std: float | None
    spend_std: float | None

    dominant_failure: str | None


@dataclass
class TrialRow:
    experiment_id: int
    case: str
    date: str
    time: str
    run: str
    trial_id: str

    # core
    status: str
    runtime: float | None

    # classification
    failure_category: str | None
    failure_detail: str | None

    # metrics
    spend_basis: float | None
    total_spend_real: float | None
    bequest_real: float | None

    # complexity
    nvars: float | None
    ncons: float | None
    nnz: float | None
    int_ratio: float | None

    # location
    path: Path
