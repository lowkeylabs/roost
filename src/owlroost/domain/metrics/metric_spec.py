from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from owlroost.domain.services.aggregation_registry import get_aggregation_explain

# =========================================================
# MetricSpec
# =========================================================

DEV_FALLBACK_ENABLED = True
EXPLAIN_FACETS = {"def", "value", "aggregation", "debug", "all"}


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
    explain_value_static: str | None = None

    interpret_series_fn: Callable[[list[Any], list[dict]], str] | None = None
    explain_value_fn: Callable[[Any, dict], str] | None = None

    def has_value_explanation(self, values: list[Any]) -> bool:
        if len(values) > 1:
            return self.interpret_series_fn is not None
        return bool(self.explain_value_fn or self.explain_value_static)

    def supports_facet(self, facet: str, values: list[Any]) -> bool:
        if facet == "def":
            return bool(self.description)

        if facet == "value":
            return self.has_value_explanation(values)

        if facet == "aggregation":
            return True  # depends on rm, handled externally

        if facet == "debug":
            return True

        return False

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

    def missing_explain_hints(
        self,
        explain: set[str],
        values: list[Any],
        rows: list[dict],
        rm=None,  # optional for aggregation context
    ) -> list[str]:
        """
        Return actionable hints for missing explanation facets.
        """

        hints = []

        key = self.key

        # ----------------------------------------
        # DEF
        # ----------------------------------------
        if "def" in explain and not self.description:
            hints.append(f"MetricSpec('{key}'): add description=... in metric_definitions.py")

        # ----------------------------------------
        # VALUE
        # ----------------------------------------
        if "value" in explain:
            if len(values) > 1:
                if not self.interpret_series_fn:
                    hints.append(
                        f"MetricSpec('{key}'): add interpret_series_fn(values, rows) in metric_definitions.py"
                    )
            else:
                if not (self.explain_value_fn or self.explain_value_static):
                    hints.append(
                        f"MetricSpec('{key}'): add explain_value_fn(value, row) or explain_value_static=... in metric_definitions.py"
                    )

        # ----------------------------------------
        # AGGREGATION
        # ----------------------------------------
        if "aggregation" in explain and rm is not None:
            agg = getattr(rm, "aggregate", None)
            if agg:
                hints.append(
                    f"Aggregation '{agg}' for '{key}': register explain in aggregation_registry.py via register_aggregation(...)"
                )

        return hints


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


def explain_metric_series(rm, rows, explain: set[str] | None = None):
    explain = explain or set()

    if "all" in explain:
        explain = {"def", "value", "aggregation"} | ({"debug"} if "debug" in explain else set())

    if not explain:
        return ""

    spec = rm.spec
    agg = getattr(rm, "aggregate", None)
    # ----------------------------------------
    # Resolve values
    # ----------------------------------------
    values = []
    for r in rows:
        values.append(resolve_metric_value(r, rm.key, agg))

    parts = []

    # ----------------------------------------
    # DEF (definition)
    # ----------------------------------------
    if "def" in explain:
        if spec.description:
            parts.append(spec.description)

    # ----------------------------------------
    # VALUE (interpretation)
    # ----------------------------------------
    if "value" in explain:
        # Series-level preferred
        if spec.interpret_series_fn:
            try:
                parts.append(spec.interpret_series_fn(values, rows))
            except Exception:
                parts.append("⚠️ interpretation error")

        # Single value fallback
        elif len(values) == 1 and spec.explain_value_fn:
            try:
                parts.append(spec.explain_value_fn(values[0], rows[0]))
            except Exception:
                parts.append("⚠️ value explanation error")

        # Static fallback
        elif spec.explain_value_static:
            parts.append(spec.explain_value_static)

    # ----------------------------------------
    # AGGREGATION (basic support)
    # ----------------------------------------
    if "aggregation" in explain:
        if agg:
            explain_fn = get_aggregation_explain(agg)

            if explain_fn:
                try:
                    parts.append(f"{rm.key}: {explain_fn(values)}")
                except Exception:
                    parts.append(f"{rm.key}: aggregation '{agg}' (explain error)")
            else:
                parts.append(f"{rm.key}: aggregated across rows using '{agg}'")

    # ----------------------------------------
    # DEV fallback (only if nothing else)
    # ----------------------------------------
    show_debug = "debug" in explain or (not parts and DEV_FALLBACK_ENABLED)
    if show_debug:
        hints = False
        try:
            preview = values[:5]
            more = "..." if len(values) > 5 else ""

            hints = spec.missing_explain_hints(explain, values, rows, rm)

            hint_str = "\n".join(f"- {h}" for h in hints) if hints else "- no hints"

            msg = (
                f"[dim]values={preview}{more}[/dim]\n"
                f"[dim]metric='{rm.key}' explain={sorted(explain)}[/dim]\n"
                f"[dim]aggregate='{agg}'[/dim]\n"
                f"[dim]fix:[/dim]\n{hint_str}"
            )

        except Exception:
            msg = f"[dim](no explanation available) metric='{rm.key}'[/dim]"

        parts.append(msg)

    return "\n".join(parts)


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


def facet_help(explain_opts):
    msg = f"help message with facets: {EXPLAIN_FACETS}\n" f"{explain_opts}"
    return msg
