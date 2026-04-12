from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from statistics import median
from typing import Any, Literal

from ..formatting import format_value
from ..services.aggregation_registry import AggContext, get_aggregation_explain

# =========================================================
# MetricSpec
# =========================================================

DEV_FALLBACK_ENABLED = True
EMPTY_RETURN = "-"

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
    compute_level: Literal["trial", "run"] = "trial"

    # -----------------------------------------------------
    # Semantics
    # -----------------------------------------------------
    description: str | None = None
    display_row_fn: Callable[[Any, dict | None, dict | None], Any] | None = None

    # Unified meaning layer (series-based only)
    value_series_fn: Callable[[list[Any], list[Any], list[dict]], str] | None = None

    def __post_init__(self):
        # Enforce value_series_fn for all metrics
        if self.value_series_fn is None:
            self.value_series_fn = default_series_fn(self)

    # -----------------------------------------------------
    # Capability checks
    # -----------------------------------------------------
    def has_value_explanation(self, values: list[Any]) -> bool:
        return bool(self.value_series_fn)

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
        # Derived metric
        if self.compute_fn and self.compute_level == "trial":
            try:
                return self.compute_fn(data)
            except Exception:
                return None

        # Path-based extraction
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
            if not self.value_series_fn:
                hints.append(f"MetricSpec('{key}'): add value_series_fn(...)")

        if "sources" in explain and rm is not None:
            agg = getattr(rm, "aggregate", None)
            if agg:
                hints.append(
                    f"Aggregation '{agg}' for '{key}': register explain in aggregation_registry.py"
                )

        return hints

    def render_value(self, value, row=None, ctx=None, fmt_override=None):
        fmt = fmt_override or self.fmt

        try:
            if self.display_row_fn:
                result = self.display_row_fn(value, row, ctx)

                if isinstance(result, str):
                    return result

                value = result

            return format_value(value, fmt)

        except Exception:
            return format_value(value, fmt)


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
        v, _ = resolve_metric_value(r, rm.key, agg)
        values.append(v)

        rv, _ = resolve_metric_value(r, rm.key, None)
        raw_values.append(rv)

    parts = []

    # ----------------------------------------
    # VARIABLES
    # ----------------------------------------
    if "variables" in explain:
        if spec.description:
            parts.append(spec.description)

    # ----------------------------------------
    # VALUES (unified series-based)
    # ----------------------------------------
    if "values" in explain:
        try:
            fn = spec.value_series_fn or default_series_fn(spec)
            results = fn(values, raw_values, rows)
            parts.append(results)

        except Exception as e:
            parts.append("value explanation error")
            parts.append(f"\n[red]{type(e).__name__}: {e}[/red]")

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

                if n_valid is not None and n_valid <= 1:
                    parts.append("Raw metric value (from plan output)")

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
            parts.append("Raw metric value (from plan output)")

    # ----------------------------------------
    # DEBUG / FALLBACK
    # ----------------------------------------
    show_debug = "debug" in explain or (not parts and DEV_FALLBACK_ENABLED)
    if not parts:
        parts.append("-")

    if show_debug:
        try:
            preview = values[:5]
            more = "..." if len(values) > 5 else ""

            hints = spec.missing_explain_hints(explain, values, rows, rm)
            hint_str = "\n".join(f"- {h}" for h in hints) if hints else ""

            msg = (
                f"[dim]values={preview}{more}[/dim]\n"
                f"[dim]metric='{rm.key}' explain={sorted(explain)}[/dim]\n"
                f"[dim]aggregate='{agg}'[/dim]\n"
                + (f"[dim]fix:[/dim]\n{hint_str}" if hint_str else "")
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
    fmt = None

    if aggregate:
        agg_key = f"{key}_{aggregate}"
        fmt_key = f"{agg_key}__fmt"

        if agg_key in row:
            lookup_key = agg_key
            fmt = row.get(fmt_key)

    return row.get(lookup_key), fmt


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


# =========================================================
# Default series function
# =========================================================


def default_series_fn(spec):
    base_fmt = spec.fmt

    # ----------------------------------------
    # Normalize aggregate names (handles tuples)
    # ----------------------------------------
    agg_names = [a if isinstance(a, str) else a[0] for a in (spec.aggregates or [])]

    def fn(values, raw, rows):
        clean = [v for v in raw if v is not None]
        if not clean:
            return EMPTY_RETURN

        # ----------------------------------------
        # INVARIANT
        # ----------------------------------------
        if spec.is_invariant:
            return str(clean[0]) if clean else EMPTY_RETURN

        # ----------------------------------------
        # COUNT METRICS
        # ----------------------------------------
        if spec.key in ("trial", "exp", "run") or "cnt" in agg_names:
            return format_value(clean[0], base_fmt)

        # ----------------------------------------
        # BOOLEAN / SUCCESS METRICS
        # ----------------------------------------
        if spec.dtype in (bool, int) and "pct" in agg_names:
            total = len(clean)
            success = sum(1 for v in clean if v)

            if total == 0:
                return EMPTY_RETURN

            pct = success / total
            return f"{success}/{total} ({format_value(pct, 'percent')})"

        # ----------------------------------------
        # RUN COMPARISON
        # ----------------------------------------
        ctx = build_visibility_context(rows)

        if ctx["n_rows"] > 1 and ctx["trial_cnt"] is not None:
            unique = list(dict.fromkeys(clean))

            if len(unique) == 1:
                return format_value(unique[0], base_fmt)

            return f"{len(unique)} distinct values"

        # ----------------------------------------
        # NUMERIC DISTRIBUTION
        # ----------------------------------------
        if all(isinstance(v, (int, float)) for v in clean):
            if len(clean) == 1:
                return format_value(clean[0], base_fmt)

            med = median(clean)
            lo = min(clean)
            hi = max(clean)

            return (
                f"Median {format_value(med, base_fmt)}, "
                f"range {format_value(lo, base_fmt)} → {format_value(hi, base_fmt)}"
            )

        # ----------------------------------------
        # STRING / CATEGORICAL
        # ----------------------------------------
        if all(isinstance(v, str) for v in clean):
            unique = list(dict.fromkeys(clean))
            if len(unique) == 1:
                return unique[0]
            return f"{len(unique)} distinct values"

        # ----------------------------------------
        # FALLBACK
        # ----------------------------------------
        return str(clean[0])

    return fn
