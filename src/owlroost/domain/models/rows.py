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
class TrialRow:
    experiment_id: int
    case: str
    date: str
    time: str
    run: str
    trial_id: str

    # =================================================
    # Core
    # =================================================
    status: str
    runtime: float | None
    solver: str | None = None

    # =================================================
    # Failure classification
    # =================================================
    failure_category: str | None = None
    failure_detail: str | None = None

    # =================================================
    # Financial metrics
    # =================================================
    spend_basis: float | None = None
    total_spend_real: float | None = None
    bequest_real: float | None = None

    roth_conversions_real: float | None = None
    tax_ordinary_real: float | None = None
    inflation_factor: float | None = None

    # =================================================
    # Complexity
    # =================================================
    nvars: float | None = None
    ncons: float | None = None
    nnz: float | None = None
    int_ratio: float | None = None

    horizon: float | None = None
    density: float | None = None

    # =================================================
    # Diagnostics (NEW)
    # =================================================
    avg_return: float | None = None
    avg_inflation: float | None = None
    min_return: float | None = None

    withdrawal_to_spending_ratio: float | None = None
    future_withdrawal_to_spending_ratio: float | None = None

    first_year_spending: float | None = None
    first_year_withdrawals: float | None = None
    first_year_tax: float | None = None

    # =================================================
    # Failure timeline (KEY INSIGHT)
    # =================================================
    immediate_real_stress_year: int | None = None
    sustained_real_stress_year: int | None = None
    cumulative_real_failure_year: int | None = None
    peak_real_year: int | None = None

    # =================================================
    # Explainability
    # =================================================
    flags: list[str] | None = None
    notes: list[str] | None = None

    # =================================================
    # Location
    # =================================================
    path: Path | None = None
