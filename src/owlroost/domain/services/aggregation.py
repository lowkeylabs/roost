from owlroost.domain.metrics.view_registry import ResolvedMetric
from owlroost.domain.services.aggregation_registry import AGG_FUNCS


def aggregate_rows(rows: list[dict], resolved_metrics: list[ResolvedMetric]) -> dict:
    if not rows:
        return {}

    summary = {}

    # ----------------------------------------
    # Aggregations (delegated to registry)
    # ----------------------------------------
    for rm in resolved_metrics:
        if not rm.aggregate:
            continue

        agg_name = rm.aggregate

        if agg_name not in AGG_FUNCS:
            raise ValueError(f"Unknown aggregation '{agg_name}' for metric '{rm.key}'")

        func = AGG_FUNCS[agg_name]

        values = [r.get(rm.key) for r in rows if r.get(rm.key) is not None]

        if not values:
            summary[f"{rm.key}_{agg_name}"] = None
            continue

        try:
            summary[f"{rm.key}_{agg_name}"] = func(values)
        except Exception as e:
            raise RuntimeError(
                f"Aggregation '{agg_name}' failed for '{rm.key}' with values={values}"
            ) from e

    # ----------------------------------------
    # INVARIANT PROPAGATION (from metric specs)
    # ----------------------------------------
    for rm in resolved_metrics:
        if not getattr(rm.spec, "is_invariant", False):
            continue

        key = rm.key
        values = {r.get(key) for r in rows}

        if not values:
            summary[key] = None
            continue

        if len(values) > 1:
            raise ValueError(f"Invariant metric '{key}' has multiple values: {values}")

        summary[key] = next(iter(values))

    # ----------------------------------------
    # CONTEXT PROPAGATION (auto-detect invariants)
    # ----------------------------------------
    known_keys = {rm.key for rm in resolved_metrics}

    for key in rows[0].keys():
        if key in known_keys:
            continue  # already handled

        values = {r.get(key) for r in rows}

        if len(values) == 1:
            # safe invariant → propagate
            summary[key] = next(iter(values))

        # else: ignore (non-invariant context like per-trial values)

    return summary
