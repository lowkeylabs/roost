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
                        solver=adapted.get("solver"),
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
                        roth_conversions_real=adapted.get("roth_conversions_real"),
                        tax_ordinary_real=adapted.get("tax_ordinary_real"),
                        inflation_factor=adapted.get("inflation_factor"),
                        # -----------------------------
                        # Complexity metrics
                        # -----------------------------
                        nvars=adapted.get("nvars"),
                        ncons=adapted.get("ncons"),
                        nnz=adapted.get("nnz"),
                        int_ratio=adapted.get("int_ratio"),
                        horizon=adapted.get("horizon"),
                        density=adapted.get("density"),
                        # -----------------------------
                        # Diagnostics (NEW)
                        # -----------------------------
                        avg_return=adapted.get("avg_return"),
                        avg_inflation=adapted.get("avg_inflation"),
                        min_return=adapted.get("min_return"),
                        withdrawal_to_spending_ratio=adapted.get("withdrawal_to_spending_ratio"),
                        future_withdrawal_to_spending_ratio=adapted.get(
                            "future_withdrawal_to_spending_ratio"
                        ),
                        first_year_spending=adapted.get("first_year_spending"),
                        first_year_withdrawals=adapted.get("first_year_withdrawals"),
                        first_year_tax=adapted.get("first_year_tax"),
                        # -----------------------------
                        # Failure timeline (KEY)
                        # -----------------------------
                        immediate_real_stress_year=adapted.get("immediate_real_stress_year"),
                        sustained_real_stress_year=adapted.get("sustained_real_stress_year"),
                        cumulative_real_failure_year=adapted.get("cumulative_real_failure_year"),
                        peak_real_year=adapted.get("peak_real_year"),
                        # -----------------------------
                        # Explainability
                        # -----------------------------
                        flags=adapted.get("flags"),
                        notes=adapted.get("notes"),
                        # -----------------------------
                        # Location
                        # -----------------------------
                        path=trial.path,
                    )
                )

    return rows
