from owlroost.domain.metrics.metric_spec import MetricSpec
from owlroost.domain.services.aggregation_registry import AGG_FUNCS


def aggregate_rows(rows: list[dict], specs: list[MetricSpec]) -> dict:
    if not rows:
        return {}

    summary = {}

    # -------------------------------------------------
    # MetricSpec-driven aggregation
    # -------------------------------------------------
    for spec in specs:
        if not spec.aggregates:
            continue

        values = [r.get(spec.key) for r in rows if isinstance(r.get(spec.key), (int | float))]

        for agg in spec.aggregates:
            func = AGG_FUNCS.get(agg)
            if not func:
                continue

            summary[f"{spec.key}_{agg}"] = func(values)

    # -------------------------------------------------
    # Core counts
    # -------------------------------------------------
    trial_count = len(rows)
    summary["trial_count"] = trial_count

    solved = sum(1 for r in rows if r.get("status") == "solved")
    failed = sum(1 for r in rows if r.get("status") == "failed")

    summary["solved_count"] = solved
    summary["failed_count"] = failed

    # -------------------------------------------------
    # Percent metrics
    # -------------------------------------------------
    summary["success_pct"] = solved / trial_count if trial_count else 0.0
    summary["fail_pct"] = failed / trial_count if trial_count else 0.0

    return summary
