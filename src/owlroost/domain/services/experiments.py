from __future__ import annotations

import statistics
from collections import defaultdict

from owlroost.domain.models.results import Experiment
from owlroost.domain.models.rows import ExperimentRow
from owlroost.domain.services.runs import build_run_rows


def _mean_or_none(values):
    return statistics.mean(values) if values else None


def build_experiment_rows(experiments: list[Experiment]) -> list[ExperimentRow]:
    """
    Aggregate RunRow → ExperimentRow
    """
    run_rows = build_run_rows(experiments)

    grouped = defaultdict(list)

    for row in run_rows:
        key = (
            row.experiment_id,
            row.case,
            row.date,
            row.time,
        )
        grouped[key].append(row)

    experiment_rows: list[ExperimentRow] = []

    for key, rows in grouped.items():
        experiment_id, case, date, time = key

        runs = len(rows)

        trials = sum(r.trials for r in rows)
        solved = sum(r.solved for r in rows)
        failed = sum(r.failed for r in rows)
        incomplete = sum(r.incomplete for r in rows)
        slow = sum(r.slow for r in rows)

        success_rate = (solved / trials * 100) if trials else 0

        def collect(rows, attr):
            return [getattr(r, attr) for r in rows if getattr(r, attr) is not None]

        experiment_rows.append(
            ExperimentRow(
                id=experiment_id,
                case=case,
                date=date,
                time=time,
                runs=runs,
                trials=trials,
                solved=solved,
                failed=failed,
                incomplete=incomplete,
                slow=slow,
                success_rate=success_rate,
                runtime=_mean_or_none(collect(rows, "runtime")),
                spend_basis=_mean_or_none(collect(rows, "spend_basis")),
                total_spend_real=_mean_or_none(collect(rows, "total_spend_real")),
                bequest_real=_mean_or_none(collect(rows, "bequest_real")),
                nvars=_mean_or_none(collect(rows, "nvars")),
                ncons=_mean_or_none(collect(rows, "ncons")),
                nnz=_mean_or_none(collect(rows, "nnz")),
                int_ratio=_mean_or_none(collect(rows, "int_ratio")),
            )
        )

    return experiment_rows
