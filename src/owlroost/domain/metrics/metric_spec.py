from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# =========================================================
# MetricSpec
# =========================================================

DEBUG_EXPLANATIONS = True


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
    is_invariant: bool = False  # does not change across trials (e.g. problem_id)

    # -----------------------------------------------------
    # Aggregation (NEW)
    # -----------------------------------------------------
    aggregates: list[str] = field(default_factory=list)

    # -----------------------------------------------------
    # Optional derived metric
    # -----------------------------------------------------
    compute_fn: Callable[[dict], Any] | None = None

    # -----------------------------------------------------
    # Notes and more
    # -----------------------------------------------------
    description: str | None = None
    interpretation: str | None = None

    interpret_series_fn: Callable[[list[Any], list[dict]], str] | None = None

    # -----------------------------------------------------
    # Extraction
    # -----------------------------------------------------
    def extract(self, data: dict):
        if self.compute_fn:
            return self.compute_fn(data)

        if self.path is None:
            return data.get(self.key)

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


def explain_metric_series(rm, rows):
    spec = rm.spec

    values = []
    for r in rows:
        values.append(resolve_metric_value(r, rm.key, getattr(rm, "aggregate", None)))

    # Priority 1: series-level interpretation
    if spec.interpret_series_fn:
        try:
            return spec.interpret_series_fn(values, rows)
        except Exception:
            return "⚠️ interpretation error"

    # Priority 2: fallback → single value interpretation
    if len(values) == 1:
        val = values[0]

        if hasattr(spec, "explain"):
            return spec.explain(val, rows[0])

    # 3. Static fallback
    if getattr(spec, "interpretation", None):
        return spec.interpretation

    if getattr(spec, "description", None):
        return spec.description

    # 4. DEFAULT DEV FALLBACK 👇
    # Show values + hint for developer
    try:
        # shorten values for readability
        preview = values[:5]
        more = "..." if len(values) > 5 else ""

        return_string = f"values={preview}{more} → add interpret_series_fn to '{rm.key}'"
    except Exception:
        return_string = f"(no interpretation) → add interpret_series_fn to '{rm.key}'"

    if DEBUG_EXPLANATIONS:
        return return_string
    else:
        return ""


def resolve_metric_value(row: dict, key: str, aggregate: str | None):
    """
    Resolve value from row, handling aggregate suffixes.
    """
    lookup_key = key

    if aggregate:
        agg_key = f"{key}_{aggregate}"
        if agg_key in row:
            lookup_key = agg_key

    return row.get(lookup_key)
