from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# =========================================================
# MetricSpec
# =========================================================


@dataclass(slots=True)
class MetricSpec:
    """
    Defines a single metric extracted from _metrics.json.

    This is the canonical definition used to:
        - extract values from JSON
        - render columns in CLI
        - enable aggregation (future)
    """

    # -----------------------------------------------------
    # Identity
    # -----------------------------------------------------
    key: str  # unique key (e.g. "spending_total_today")
    label: str

    # -----------------------------------------------------
    # Extraction location (or none if derived)
    # -----------------------------------------------------
    path: str | None = None  # dot path in JSON (e.g. "financial.spending.total.today")

    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------
    fmt: str = "default"  # formatting key (reuse format_value)
    align: str = "right"

    # -----------------------------------------------------
    # Typing / semantics
    # -----------------------------------------------------
    dtype: type = float  # float, int, str, bool
    category: str = "general"  # financial, risk, timing, etc.

    # -----------------------------------------------------
    # Behavior flags
    # -----------------------------------------------------
    is_timeseries: bool = False
    is_required: bool = False

    # -----------------------------------------------------
    # Aggregation (NEW)
    # -----------------------------------------------------
    aggregates: list[str] = field(default_factory=list)

    # -----------------------------------------------------
    # Optional derived metric (NOT used yet)
    # -----------------------------------------------------
    compute_fn: Callable[[dict], Any] | None = None

    # -----------------------------------------------------
    # Extraction
    # -----------------------------------------------------
    def extract(self, data: dict) -> Any:
        """
        Extract value from nested dict using path.
        """
        if self.path is None:
            # already flat dict (e.g., aggregated data)
            return data.get(self.key)

        if self.compute_fn:
            return self.compute_fn(data)

        current = data
        for part in self.path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)

        return current


# =========================================================
# Helpers
# =========================================================


def extract_metrics(data: dict, specs: list[MetricSpec]) -> dict:
    """
    Extract all metrics into a flat dict.
    """
    row = {}

    for spec in specs:
        try:
            value = spec.extract(data)
        except Exception:
            value = None

        row[spec.key] = value

    return row
