from __future__ import annotations

from owlroost.domain.models.results import Experiment
from owlroost.domain.models.rows import TrialRow
from owlroost.domain.services.metrics_adapter import adapt_metrics


def build_trial_rows(experiments: list[Experiment]) -> list[TrialRow]:
    """
    Convert Experiment → Run → Trial into flat TrialRow records.

    This is the canonical extraction layer for all trial-level views.

    Uses metrics_adapter as the ONLY schema-aware component.
    """
    rows: list[TrialRow] = []

    for exp in experiments:
        for run in exp.runs:
            for trial in run.trials:
                # -------------------------------------------------
                # Adapt raw JSON → canonical flat structure
                # -------------------------------------------------
                adapted = adapt_metrics(trial.data)

                # -------------------------------------------------
                # Core fields with fallback
                # -------------------------------------------------
                runtime = adapted.get("runtime") or trial.runtime

                status = adapted.get("status") or trial.status
                status = (status or "").upper()

                # -------------------------------------------------
                # Failure classification (robust)
                # -------------------------------------------------
                failure_category = adapted.get("failure_category")
                if status == "FAILED" and not failure_category:
                    failure_category = "unknown_failure"

                # -------------------------------------------------
                # Build TrialRow (ALL values from adapter)
                # -------------------------------------------------
                rows.append(
                    TrialRow(
                        experiment_id=exp.id,
                        case=exp.case,
                        date=exp.date,
                        time=exp.time,
                        run=run.name,
                        trial_id=trial.path.name,
                        # -----------------------------
                        # Core
                        # -----------------------------
                        runtime=runtime,
                        status=status,
                        # -----------------------------
                        # Failure classification
                        # -----------------------------
                        failure_category=failure_category,
                        failure_detail=adapted.get("failure_detail"),
                        # -----------------------------
                        # Financial metrics
                        # -----------------------------
                        spend_basis=adapted.get("spend_basis"),
                        total_spend_real=adapted.get("total_spend_real"),
                        bequest_real=adapted.get("bequest_real"),
                        # -----------------------------
                        # Complexity metrics
                        # -----------------------------
                        nvars=adapted.get("nvars"),
                        ncons=adapted.get("ncons"),
                        nnz=adapted.get("nnz"),
                        int_ratio=adapted.get("int_ratio"),
                        # -----------------------------
                        # Location
                        # -----------------------------
                        path=trial.path,
                    )
                )

    return rows
