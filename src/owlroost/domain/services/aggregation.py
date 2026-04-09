from loguru import logger

from owlroost.domain.metrics.metric_registry import METRIC_REGISTRY
from owlroost.domain.services.aggregation_registry import AGG_DEFAULT_FMT, AGG_FUNCS


def aggregate_rows(rows: list[dict]) -> dict:
    if not rows:
        return {}

    logger.trace(f"rows: {rows}")

    summary = {}

    # =====================================================
    # AGGREGATIONS (ALL METRICS WITH aggregates defined)
    # =====================================================

    for key, spec in METRIC_REGISTRY.items():
        if not spec.aggregates:
            continue

        values = []

        for r in rows:
            v = r.get(key)

            # -------------------------------------------------
            # FALLBACK TO compute_fn IF VALUE MISSING
            # -------------------------------------------------
            if v is None and spec.compute_fn:
                try:
                    v = spec.compute_fn(r)
                except Exception:
                    v = None

            if v is not None and isinstance(v, (int | float)):
                values.append(v)

        for agg_name, fmt in _normalize_aggregates(spec.aggregates, spec.fmt):
            if agg_name not in AGG_FUNCS:
                raise ValueError(f"Unknown aggregation '{agg_name}' for metric '{key}'")

            n = len(values)

            # -----------------------------------------
            # Record sample size
            # -----------------------------------------
            summary[f"{key}_{agg_name}_n"] = n

            if n == 0:
                summary[f"{key}_{agg_name}"] = None
                continue

            try:
                func = AGG_FUNCS[agg_name]
                summary[f"{key}_{agg_name}"] = func(values)
                summary[f"{key}_{agg_name}__fmt"] = fmt
            except Exception as e:
                raise RuntimeError(
                    f"Aggregation '{agg_name}' failed for '{key}' with values={values}"
                ) from e

    # =====================================================
    # INVARIANT PROPAGATION
    # =====================================================

    for key, spec in METRIC_REGISTRY.items():
        if not getattr(spec, "is_invariant", False):
            continue

        values = [r.get(key) for r in rows if r.get(key) is not None]

        if not values:
            summary[key] = None
            continue

        first = values[0]

        # -------------------------------------------------
        # HANDLE DICTS (e.g., overrides)
        # -------------------------------------------------
        if isinstance(first, dict):
            if all(v == first for v in values):
                summary[key] = first
            else:
                # Should not happen, but safe fallback
                summary[key] = first
            continue

        # -------------------------------------------------
        # HANDLE HASHABLE VALUES (existing behavior)
        # -------------------------------------------------
        hashable_values = {v for v in values if _is_hashable(v)}

        if not hashable_values:
            summary[key] = None
            continue

        if len(hashable_values) > 1:
            raise ValueError(f"Invariant metric '{key}' has multiple values: {hashable_values}")

        summary[key] = next(iter(hashable_values))

    # =====================================================
    # CONTEXT PROPAGATION (auto-detect invariants)
    # =====================================================

    for key in rows[0].keys():
        if key in summary:
            continue  # already handled

        values = {v for r in rows if (v := r.get(key)) is not None and _is_hashable(v)}

        if len(values) == 1:
            summary[key] = next(iter(values))

    return summary


# =====================================================
# Helpers
# =====================================================


def _is_hashable(v):
    try:
        hash(v)
        return True
    except TypeError:
        return False


def _normalize_aggregates(aggregates, spec_fmt):
    result = []

    for a in aggregates:
        if isinstance(a, tuple):
            name, fmt = a
        else:
            name = a
            fmt = AGG_DEFAULT_FMT.get(name) or spec_fmt

        result.append((name, fmt))

    return result
