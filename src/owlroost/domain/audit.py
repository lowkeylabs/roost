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
