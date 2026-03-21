from loguru import logger

from owlroost.domain.metrics.metric_registry import METRIC_REGISTRY
from owlroost.domain.services.aggregation_registry import AGG_FUNCS


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
        values = [r.get(key) for r in rows if r.get(key) is not None]

        for agg_name in spec.aggregates:
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

        values = {r.get(key) for r in rows}

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

        values = {r.get(key) for r in rows}

        if len(values) == 1:
            summary[key] = next(iter(values))

    return summary
