from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..services.aggregation_registry import AggContext, get_aggregation_explain

# =========================================================
# MetricSpec
# =========================================================

DEV_FALLBACK_ENABLED = True

EXPLAIN_FACETS = {
    "variables",
    "values",
    "sources",
    "debug",
    "all",
}

# Backward compatibility (optional safety)
FACET_ALIASES = {
    "def": "variables",
    "value": "values",
    "aggregation": "sources",
}


@dataclass(slots=True)
class MetricSpec:
    """
    Defines a single metric extracted from _metrics.json.
    """

    # -----------------------------------------------------
    # Identity
    # -----------------------------------------------------
    key: str
    label: str

    # -----------------------------------------------------
    # Extraction
    # -----------------------------------------------------
    path: str | None = None

    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------
    fmt: str = "default"
    align: str = "right"

    # -----------------------------------------------------
    # Typing / semantics
    # -----------------------------------------------------
    dtype: type = float
    category: str = "general"

    # -----------------------------------------------------
    # Behavior flags
    # -----------------------------------------------------
    is_timeseries: bool = False
    is_required: bool = False
    is_invariant: bool = False

    # -----------------------------------------------------
    # Visibility
    # -----------------------------------------------------
    show_if: Callable[[dict], bool] | None = None

    # -----------------------------------------------------
    # Aggregation
    # -----------------------------------------------------
    aggregates: list[str] = field(default_factory=list)

    # -----------------------------------------------------
    # Derived metric
    # -----------------------------------------------------
    compute_fn: Callable[[dict], Any] | None = None

    # -----------------------------------------------------
    # Semantics
    # -----------------------------------------------------
    description: str | None = None

    # Legacy (kept for compatibility)
    explain_value_static: str | None = None
    explain_value_fn: Callable[[Any, dict], str] | None = None

    # Primary meaning layer (preferred going forward)
    value_fn: Callable[[Any, dict], str] | None = None
    value_series_fn: Callable[[list[Any], list[dict]], str] | None = None

    # -----------------------------------------------------
    # Capability checks
    # -----------------------------------------------------
    def has_value_explanation(self, values: list[Any]) -> bool:
        return bool(
            self.value_fn
            or self.value_series_fn
            or self.explain_value_fn
            or self.explain_value_static
        )

    def supports_facet(self, facet: str, values: list[Any]) -> bool:
        if facet == "variables":
            return bool(self.description)

        if facet == "values":
            return self.has_value_explanation(values)

        if facet == "sources":
            return True

        if facet == "debug":
            return True

        return False

    # -----------------------------------------------------
    # Extraction
    # -----------------------------------------------------
    def extract(self, data: dict):
        """
        Resolve value for this metric.

        Priority:
            1. compute_fn (derived metric)
            2. path (raw extraction)
            3. None
        """
        # ----------------------------------------
        # Derived metric (takes precedence)
        # ----------------------------------------
        if self.compute_fn:
            try:
                return self.compute_fn(data)
            except Exception:
                return None

        # ----------------------------------------
        # Path-based extraction
        # ----------------------------------------
        if not self.path:
            return None

        try:
            value = data
            for part in self.path.split("."):
                if value is None:
                    return None
                value = value.get(part)
            return value
        except Exception:
            return None

    # -----------------------------------------------------
    # Dev hints
    # -----------------------------------------------------
    def missing_explain_hints(
        self,
        explain: set[str],
        values: list[Any],
        rows: list[dict],
        rm=None,
    ) -> list[str]:
        hints = []
        key = self.key

        if "variables" in explain and not self.description:
            hints.append(f"MetricSpec('{key}'): add description=...")

        if "values" in explain:
            if not self.has_value_explanation(values):
                hints.append(f"MetricSpec('{key}'): add value_fn(...) or value_series_fn(...)")

        if "sources" in explain and rm is not None:
            agg = getattr(rm, "aggregate", None)
            if agg:
                hints.append(
                    f"Aggregation '{agg}' for '{key}': register explain in aggregation_registry.py"
                )

        return hints


# =========================================================
# Helpers
# =========================================================


def extract_metrics(data: dict, specs: list[MetricSpec]) -> dict:
    row = {}

    for spec in specs:
        try:
            value = spec.extract(data)
        except Exception:
            value = None

        row[spec.key] = value

    return row


# =========================================================
# Explain Engine
# =========================================================


def explain_metric_series(rm, rows, explain: set[str] | None = None):
    explain = explain or set()

    # normalize aliases
    explain = {FACET_ALIASES.get(f, f) for f in explain}

    if "all" in explain:
        explain = {"variables", "values", "sources"} | ({"debug"} if "debug" in explain else set())

    if not explain:
        return ""

    spec = rm.spec
    agg = getattr(rm, "aggregate", None)

    # ----------------------------------------
    # Resolve values
    # ----------------------------------------
    values = []
    raw_values = []

    for r in rows:
        values.append(resolve_metric_value(r, rm.key, agg))
        raw_values.append(resolve_metric_value(r, rm.key, None))

    parts = []

    # ----------------------------------------
    # VARIABLES
    # ----------------------------------------
    if "variables" in explain:
        if spec.description:
            parts.append(spec.description)

    # ----------------------------------------
    # VALUES (primary meaning layer)
    # ----------------------------------------
    if "values" in explain:
        try:
            if len(values) > 1 and spec.value_series_fn:
                parts.append(spec.value_series_fn(values, rows))

            elif len(values) == 1 and spec.value_fn:
                parts.append(spec.value_fn(values[0], rows[0]))

            elif len(values) == 1 and spec.explain_value_fn:
                parts.append(spec.explain_value_fn(values[0], rows[0]))

            elif spec.explain_value_static:
                parts.append(spec.explain_value_static)

        except Exception:
            parts.append("value explanation error")

    # ----------------------------------------
    # SOURCES
    # ----------------------------------------
    if "sources" in explain:
        if agg:
            explain_fn = get_aggregation_explain(agg)

            try:
                n_total = None
                n_valid = None

                if rows and isinstance(rows[0], dict):
                    n_total = rows[0].get("trial_cnt")
                    n_valid = rows[0].get(f"{rm.key}_{agg}_n")

                # ✅ KEY FIX: treat single observation as raw
                if n_valid is not None and n_valid <= 1:
                    parts.append("Raw value from metrics")

                elif explain_fn:
                    ctx = AggContext(
                        agg_values=values,
                        n_total=n_total,
                        n_valid=n_valid,
                        aggregation=agg,
                        metric_key=rm.key,
                    )
                    parts.append(explain_fn(ctx))

                else:
                    parts.append(f"Aggregated using '{agg}'")

            except Exception:
                parts.append(f"Aggregated using '{agg}'")

        else:
            parts.append("Raw value from metrics")

    # ----------------------------------------
    # DEBUG / FALLBACK
    # ----------------------------------------
    show_debug = "debug" in explain or (not parts and DEV_FALLBACK_ENABLED)

    if show_debug:
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


# =========================================================
# Value Resolver
# =========================================================


def resolve_metric_value(row: dict, key: str, aggregate: str | None):
    lookup_key = key

    if aggregate:
        agg_key = f"{key}_{aggregate}"
        if agg_key in row:
            lookup_key = agg_key

    return row.get(lookup_key)


# =========================================================
# CLI Help
# =========================================================


def facet_help(explain_opts):
    return (
        "Explain facets:\n"
        "  variables  → definition of the metric\n"
        "  values     → meaning of the result\n"
        "  sources    → how the value was derived\n"
        f"\nAvailable: {sorted(EXPLAIN_FACETS)}\n"
        f"{explain_opts}"
    )


# =========================================================
# Visibility Context
# =========================================================


def build_visibility_context(rows: list[dict]) -> dict:
    n = len(rows)

    trial_cnt = None
    if rows and isinstance(rows[0], dict):
        trial_cnt = rows[0].get("trial_cnt")

    if trial_cnt is not None:
        is_single = trial_cnt == 1
        is_stochastic = trial_cnt > 1
    else:
        is_single = n == 1
        is_stochastic = n > 1

    return {
        "n_rows": n,
        "trial_cnt": trial_cnt,
        "is_single": is_single,
        "is_stochastic": is_stochastic,
    }
