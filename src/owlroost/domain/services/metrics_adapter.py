from __future__ import annotations

from typing import Any

SUPPORTED_SCHEMAS = {"roost.metrics.v1"}


def adapt_metrics(data: dict | None) -> dict:
    """
    Convert raw metrics.json → canonical flat structure.

    This is the ONLY place that knows the JSON schema.

    Output keys are aligned with TrialRow fields.

    Safe behavior:
    - Missing sections → {}
    - Missing values → None
    - Unknown schema → raises ValueError (fail fast)
    """

    if not data:
        return {}

    # -------------------------------------------------
    # Schema validation
    # -------------------------------------------------
    schema = data.get("schema")
    if schema not in SUPPORTED_SCHEMAS:
        raise ValueError(f"Unsupported metrics schema: {schema}")

    # -------------------------------------------------
    # Extract sections (safe defaults)
    # -------------------------------------------------
    metrics: dict[str, Any] = data.get("metrics") or {}
    complexity: dict[str, Any] = data.get("complexity") or {}
    timing: dict[str, Any] = data.get("timing") or {}
    run_status: dict[str, Any] = data.get("run_status") or {}
    diagnostics: dict[str, Any] = data.get("diagnostics") or {}
    rate_fail: dict[str, Any] = diagnostics.get("rate_driven_failures") or {}

    # -------------------------------------------------
    # Normalize values
    # -------------------------------------------------
    status_raw = run_status.get("status")
    status = (status_raw or "").upper() if status_raw else None

    runtime = timing.get("elapsed_seconds")

    # -------------------------------------------------
    # Build canonical flat structure
    # -------------------------------------------------
    return {
        # =================================================
        # Core
        # =================================================
        "runtime": runtime,
        "status": status,
        "solver": data.get("solver"),
        # =================================================
        # Failure classification
        # =================================================
        "failure_category": run_status.get("failure_category"),
        "failure_detail": run_status.get("failure_detail"),
        # =================================================
        # Financial metrics (metrics section ONLY)
        # =================================================
        "spend_basis": metrics.get("net_yearly_spending_basis"),
        "total_spend_real": metrics.get("total_net_spending_real"),
        "bequest_real": metrics.get("total_final_bequest_real"),
        # Optional extended metrics
        "roth_conversions_real": metrics.get("total_roth_conversions_real"),
        "tax_ordinary_real": metrics.get("total_tax_ordinary_real"),
        "inflation_factor": metrics.get("final_inflation_factor"),
        # =================================================
        # Complexity metrics
        # =================================================
        "nvars": complexity.get("num_decision_variables"),
        "ncons": complexity.get("num_constraints"),
        "nnz": complexity.get("num_nonzeros"),
        "int_ratio": complexity.get("integer_variable_ratio"),
        # Optional extended complexity
        "horizon": complexity.get("horizon"),
        "density": complexity.get("matrix_density"),
        # =================================================
        # Diagnostics (🔥 NEW — high value)
        # =================================================
        "avg_return": diagnostics.get("avg_return"),
        "avg_inflation": diagnostics.get("avg_inflation"),
        "min_return": diagnostics.get("min_return"),
        # Spending pressure
        "withdrawal_to_spending_ratio": diagnostics.get("withdrawal_to_spending_ratio"),
        "future_withdrawal_to_spending_ratio": diagnostics.get(
            "future_withdrawal_to_spending_ratio"
        ),
        # First-year signals
        "first_year_spending": diagnostics.get("first_year_spending"),
        "first_year_withdrawals": diagnostics.get("first_year_withdrawals"),
        "first_year_tax": diagnostics.get("first_year_tax"),
        # =================================================
        # Rate-driven failure timeline (🔥 KEY)
        # =================================================
        "immediate_real_stress_year": rate_fail.get("immediate_real_stress_year"),
        "sustained_real_stress_year": rate_fail.get("sustained_real_stress_year"),
        "cumulative_real_failure_year": rate_fail.get("cumulative_real_failure_year"),
        "peak_real_year": rate_fail.get("peak_real_year"),
        # =================================================
        # Flags + Notes (🔥 EXPLAINABILITY)
        # =================================================
        "flags": diagnostics.get("flags"),
        "notes": diagnostics.get("notes"),
    }
