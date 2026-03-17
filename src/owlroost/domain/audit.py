from dataclasses import dataclass


@dataclass
class AuditRow:
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

    # --- NEW (aggregated from trials) ---
    runtime: float | None = None
    spend_basis: float | None = None
    total_spend_real: float | None = None
    bequest_real: float | None = None

    nvars: int | None = None
    ncons: int | None = None
    nnz: int | None = None
    int_ratio: float | None = None
