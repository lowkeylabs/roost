from loguru import logger

from owlroost.domain.metrics.metric_registry import METRIC_REGISTRY
from owlroost.domain.services.aggregation_registry import AGG_DEFAULT_FMT, AGG_FUNCS


def aggregate_rows(rows: list[dict]) -> dict:
    if not rows:
        return {}

    logger.debug(rows)

    summary = {}

    # =====================================================
    # AGGREGATIONS (ALL METRICS WITH aggregates defined)
    # =====================================================

    for key, spec in METRIC_REGISTRY.items():
        if not spec.aggregates:
            continue

        # Only valid (non-null) values
        values = [v for r in rows if (v := r.get(key)) is not None and isinstance(v, (int | float))]

        for agg_name, fmt in _normalize_aggregates(spec.aggregates, spec.fmt):
            if agg_name not in AGG_FUNCS:
                raise ValueError(f"Unknown aggregation '{agg_name}' for metric '{key}'")

            n = len(values)

            # -----------------------------------------
            # Record sample size for this aggregation
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
    # INVARIANT PROPAGATION (explicit)
    # =====================================================

    for key, spec in METRIC_REGISTRY.items():
        if not getattr(spec, "is_invariant", False):
            continue

        values = {v for r in rows if (v := r.get(key)) is not None and _is_hashable(v)}

        if not values:
            summary[key] = None
            continue

        if len(values) > 1:
            raise ValueError(f"Invariant metric '{key}' has multiple values: {values}")

        summary[key] = next(iter(values))

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
