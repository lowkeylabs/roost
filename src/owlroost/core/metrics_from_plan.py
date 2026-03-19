import json
from datetime import datetime
from pathlib import Path

import numpy as np
from owlplanner.export import build_summary_dic


def _mosek_available():
    import importlib.util
    import os

    return (
        importlib.util.find_spec("mosek") is not None
        and os.environ.get("MOSEKLM_LICENSE_FILE") is not None
    )


def normalize_timestamp(ts) -> str:
    """
    Return an ISO-8601 timestamp string from either
    a datetime or a string.
    """
    if isinstance(ts, datetime):
        return ts.isoformat()
    if isinstance(ts, str):
        return ts
    raise TypeError(f"Unsupported timestamp type: {type(ts)}")


def xxxmetrics_from_plan(plan) -> dict:
    # using owlplanner.export.build_summary_dic to get metrics.
    # these are formatted for output, not analysis.
    dic = build_summary_dic(plan)
    return dic


def metrics_from_plan(plan, N=None) -> dict:
    # Original code found in: owlplanner.export.py

    if N is None:
        N = plan.N_n
    if not (0 < N <= plan.N_n):
        raise ValueError(f"Value N={N} is out of reange")

    start_year = int(plan.year_n[0])
    final_year = int(plan.year_n[-1])

    m = {
        "plan_name": plan._name,
        "run_timestamp": normalize_timestamp(plan._timestamp),
        "plan_start_date": str(plan.startDate),
        # horizon
        "year_start": start_year,
        "year_final_bequest": final_year,
        # model size
        "num_decision_variables": int(plan.A.nvars),
        "num_constraints": int(plan.A.ncons),
        # inflation
        "final_inflation_factor": float(plan.gamma_n[-1]),
    }

    m["net_yearly_spending_basis"] = plan.g_n[0] / plan.xi_n[0]
    m["net_yearly_spending_in_first_year"] = plan.g_n[0]
    m["net_spending_for_plan_year_0"] = plan.g_n[0]

    # nominal vs real values are based on the inflation factor gamma_n,
    #   which is the cumulative product of (1 + inflation_rate) over time.

    # Nominal values are in the dollars of the year they occur,
    # Real values are adjusted to the dollars of the first year (year 0) by dividing by gamma_n.

    # ---- totals: spending ----
    totSpending = np.sum(plan.g_n[:N], axis=0)
    totSpendingNow = np.sum(plan.g_n[:N] / plan.gamma_n[:N], axis=0)
    m["total_net_spending_nominal"] = float(totSpending)
    m["total_net_spending_real"] = float(totSpendingNow)

    # ---- totals: Roth conversions ----
    totRoth = np.sum(plan.x_in[:, :N], axis=(0, 1))
    totRothNow = np.sum(np.sum(plan.x_in[:, :N], axis=0) / plan.gamma_n[:N], axis=0)
    m["total_roth_conversions_nominal"] = float(totRoth)
    m["total_roth_conversions_real"] = float(totRothNow)

    # ---- totals: taxes ----
    taxPaid = np.sum(plan.T_n[:N], axis=0)
    taxPaidNow = np.sum(plan.T_n[:N] / plan.gamma_n[:N], axis=0)
    m["total_tax_ordinary_nominal"] = float(taxPaid)
    m["total_tax_ordinary_real"] = float(taxPaidNow)

    # ---- totals: estate ----
    estate = np.sum(plan.b_ijn[:, :, plan.N_n], axis=0)
    # heirsTaxLiability = (estate[1] + estate[3]) * plan.nu  # tax-deferred and HSA
    estate[1] *= 1 - plan.nu  # tax-deferred: heirs pay ordinary income tax
    estate[3] *= 1 - plan.nu  # HSA: non-spouse heirs include full balance in ordinary income
    # endyear = plan.year_n[-1]
    lyNow = 1.0 / plan.gamma_n[-1]
    debts = plan.remaining_debt_balance
    savingsEstate = np.sum(estate)
    totEstate = savingsEstate - debts + plan.fixed_assets_bequest_value

    m["total_final_bequest_nominal"] = float(totEstate)
    m["total_final_bequest_real"] = float(totEstate * lyNow)

    return m


def complexity_from_plan(plan) -> dict:
    """
    Extract structural complexity metrics from a solved plan.

    These metrics describe the size and structure of the LP/MILP
    independent of financial outcomes.
    """

    A = plan.A
    B = plan.B

    nvars = int(A.nvars)
    ncons = int(A.ncons)

    # -----------------------------------------
    # Core size
    # -----------------------------------------
    nnz = sum(len(row) for row in A.Aind)

    # -----------------------------------------
    # Density
    # -----------------------------------------
    density = nnz / (nvars * ncons) if nvars and ncons else None

    # -----------------------------------------
    # Integer structure (MILP complexity)
    # -----------------------------------------
    try:
        num_integer_vars = len(B.integralityList())
    except Exception:
        num_integer_vars = None

    # -----------------------------------------
    # Horizon (time dimension)
    # -----------------------------------------
    year_start = int(plan.year_n[0])
    year_final = int(plan.year_n[-1])
    horizon = year_final - year_start

    # -----------------------------------------
    # Derived metrics (very useful diagnostically)
    # -----------------------------------------
    nnz_per_var = nnz / nvars if nvars else None
    nnz_per_cons = nnz / ncons if ncons else None
    int_ratio = num_integer_vars / nvars if (num_integer_vars is not None and nvars) else None

    return {
        # --- size ---
        "num_decision_variables": nvars,
        "num_constraints": ncons,
        "num_nonzeros": int(nnz),
        # --- structure ---
        "matrix_density": float(density) if density is not None else None,
        # --- MILP complexity ---
        "num_integer_variables": int(num_integer_vars) if num_integer_vars is not None else None,
        "integer_variable_ratio": float(int_ratio) if int_ratio is not None else None,
        # --- time dimension ---
        "horizon": int(horizon),
        # --- derived ---
        "nnz_per_variable": float(nnz_per_var) if nnz_per_var is not None else None,
        "nnz_per_constraint": float(nnz_per_cons) if nnz_per_cons is not None else None,
    }


def classify_run_status_from_plan(plan, diagnostics: dict | None = None) -> dict:
    """
    Returns structured run status classification using diagnostics-driven logic.
    Avoids recomputing diagnostics if already available.
    """

    case_status = (plan.caseStatus or "").lower()
    conv = (getattr(plan, "convergenceType", "") or "").lower()

    # -----------------------------------------
    # Use provided diagnostics or compute once
    # -----------------------------------------
    if diagnostics is None:
        diagnostics = diagnostics_from_plan(plan)

    flags = diagnostics.get("flags", [])

    # --------------------------------------------------
    # SUCCESS
    # --------------------------------------------------
    if case_status == "solved":
        return {
            "status": "solved",
            "failure_category": None,
            "failure_detail": None,
        }

    # --------------------------------------------------
    # ECONOMIC INFEASIBILITY (primary path)
    # --------------------------------------------------
    if any(
        f in flags
        for f in [
            "cumulative_real_erosion",
            "future_real_return_deficit",
            "sustained_real_return_stress",
        ]
    ):
        return {
            "status": "failed",
            "failure_category": "economic_infeasibility",
            "failure_detail": "negative_real_return_environment",
        }

    # --------------------------------------------------
    # WITHDRAWAL / TAX PRESSURE
    # --------------------------------------------------
    if any(
        f in flags
        for f in [
            "extreme_withdrawal_pressure",
            "future_withdrawal_pressure",
        ]
    ):
        return {
            "status": "failed",
            "failure_category": "economic_infeasibility",
            "failure_detail": "withdrawal_pressure",
        }

    # --------------------------------------------------
    # LIQUIDITY FAILURE
    # --------------------------------------------------
    if "insufficient_liquidity" in flags:
        return {
            "status": "failed",
            "failure_category": "economic_infeasibility",
            "failure_detail": "liquidity_shortfall",
        }

    # --------------------------------------------------
    # SOLVER FAILURE
    # --------------------------------------------------
    if conv in ("undefined", "", None):
        return {
            "status": "failed",
            "failure_category": "solver_failure",
            "failure_detail": "no_feasible_solution",
        }

    # --------------------------------------------------
    # NO CONVERGENCE
    # --------------------------------------------------
    if "max iteration" in conv:
        return {
            "status": "failed",
            "failure_category": "no_convergence",
            "failure_detail": "max_iterations",
        }

    if "oscillatory" in conv:
        return {
            "status": "failed",
            "failure_category": "no_convergence",
            "failure_detail": "oscillation",
        }

    # --------------------------------------------------
    # FALLBACK
    # --------------------------------------------------
    return {
        "status": "failed",
        "failure_category": "infeasible_constraints",
        "failure_detail": "unknown",
    }


def diagnostics_from_plan(plan) -> dict:
    tau = plan.tau_kn

    # -----------------------------------------
    # Returns
    # -----------------------------------------
    stock_returns = tau[0]

    avg_return = float(np.mean(stock_returns))
    min_return = float(np.min(stock_returns))

    first5_avg = float(np.mean(stock_returns[:5]))
    first10_avg = float(np.mean(stock_returns[:10]))

    worst_drawdown = float(np.min(np.cumprod(1 + stock_returns)))

    # -----------------------------------------
    # Inflation
    # -----------------------------------------
    inflation = tau[3]
    avg_inflation = float(np.mean(inflation))

    # -----------------------------------------
    # REAL RETURNS (🔥 CORE SIGNAL)
    # -----------------------------------------
    real_returns = (1 + stock_returns) / (1 + inflation) - 1
    real_growth = np.cumprod(1 + real_returns)

    # --- immediate stress (point-in-time)
    immediate_real_stress_year = None
    for i, r in enumerate(real_returns):
        if r < 0:
            immediate_real_stress_year = i
            break

    # --- sustained stress (rolling window)
    sustained_real_stress_year = None
    window = 5
    for i in range(len(real_returns) - window + 1):
        if np.mean(real_returns[i : i + window]) < 0:
            sustained_real_stress_year = i
            break

    # --- cumulative erosion
    real_failure_year = None
    for i, val in enumerate(real_growth):
        if val < 0.9:
            real_failure_year = i
            break

    # --- peak year
    peak_real_year_index = int(np.argmax(real_growth)) if len(real_growth) > 0 else None

    # -----------------------------------------
    # Spending & withdrawals (year 0)
    # -----------------------------------------
    spending = None
    withdrawals = None
    tax = None
    withdrawal_to_spending_ratio = None

    if hasattr(plan, "g_n") and len(plan.g_n) > 0:
        spending = float(plan.g_n[0])

    w = None
    if hasattr(plan, "w_ijn"):
        w = np.sum(plan.w_ijn, axis=(0, 1))
        if len(w) > 0:
            withdrawals = float(w[0])

    if hasattr(plan, "T_n") and len(plan.T_n) > 0:
        tax = float(plan.T_n[0])

    if spending and withdrawals:
        withdrawal_to_spending_ratio = withdrawals / spending

    # -----------------------------------------
    # Forward-looking diagnostics (years 1–5)
    # -----------------------------------------
    future_spending = None
    future_withdrawals = None
    future_ratio = None

    if hasattr(plan, "g_n") and len(plan.g_n) > 5:
        future_spending = float(np.mean(plan.g_n[1:6]))

    if w is not None and len(w) > 5:
        future_withdrawals = float(np.mean(w[1:6]))

    if future_spending and future_withdrawals:
        future_ratio = future_withdrawals / future_spending

    # -----------------------------------------
    # Year mapping
    # -----------------------------------------
    year0 = int(plan.year_n[0]) if hasattr(plan, "year_n") else None

    def to_year(idx):
        return int(year0 + idx) if (year0 is not None and idx is not None) else None

    # -----------------------------------------
    # Flags
    # -----------------------------------------
    flags = []

    if first5_avg < 0:
        flags.append("negative_early_sequence")

    if min_return < -0.3:
        flags.append("severe_drawdown")

    if avg_return < 0.02:
        flags.append("low_return_environment")

    if avg_inflation > 0.035:
        flags.append("high_inflation")

    if first10_avg < avg_inflation:
        flags.append("negative_real_returns_early")
        flags.append("future_real_return_deficit")

    if withdrawal_to_spending_ratio:
        if withdrawal_to_spending_ratio > 1.3:
            flags.append("high_tax_drag")
        if withdrawal_to_spending_ratio > 1.6:
            flags.append("extreme_withdrawal_pressure")

    if future_ratio and future_ratio > 1.3:
        flags.append("future_withdrawal_pressure")

    if immediate_real_stress_year is not None:
        flags.append("immediate_real_return_stress")

    if sustained_real_stress_year is not None:
        flags.append("sustained_real_return_stress")

    if real_failure_year is not None:
        flags.append("cumulative_real_erosion")

    if spending and withdrawals and withdrawals < spending:
        flags.append("insufficient_liquidity")

    # -----------------------------------------
    # Rate-driven failure summary
    # -----------------------------------------
    rate_driven_failures = {
        "immediate_real_stress_year": to_year(immediate_real_stress_year),
        "sustained_real_stress_year": to_year(sustained_real_stress_year),
        "cumulative_real_failure_year": to_year(real_failure_year),
        "peak_real_year": to_year(peak_real_year_index),
        "real_growth_first10": real_growth[:10].tolist(),
        "real_return_first10": real_returns[:10].tolist(),
    }

    # -----------------------------------------
    # Human-readable notes (🔥 NEW)
    # -----------------------------------------
    notes = []

    if avg_inflation > avg_return:
        notes.append("Average inflation exceeds average returns, leading to negative real growth.")

    if immediate_real_stress_year is not None:
        notes.append(
            f"Real returns are negative as early as year {to_year(immediate_real_stress_year)}."
        )

    if sustained_real_stress_year is not None:
        notes.append(
            f"Sustained negative real return environment begins around year {to_year(sustained_real_stress_year)}."
        )

    if real_failure_year is not None:
        notes.append(
            f"Cumulative real wealth falls below 90% of starting value by year {to_year(real_failure_year)}."
        )

    if withdrawal_to_spending_ratio and withdrawal_to_spending_ratio > 1.0:
        notes.append("Withdrawals exceed spending, indicating tax drag or inefficient liquidation.")

    # -----------------------------------------
    # Return
    # -----------------------------------------
    return {
        "avg_return": avg_return,
        "min_return": min_return,
        "first5_avg_return": first5_avg,
        "first10_avg_return": first10_avg,
        "worst_drawdown_factor": worst_drawdown,
        "avg_inflation": avg_inflation,
        "first_year_spending": spending,
        "first_year_withdrawals": withdrawals,
        "first_year_tax": tax,
        "withdrawal_to_spending_ratio": withdrawal_to_spending_ratio,
        "future_avg_spending_years_1_5": future_spending,
        "future_avg_withdrawals_years_1_5": future_withdrawals,
        "future_withdrawal_to_spending_ratio": future_ratio,
        "rate_driven_failures": rate_driven_failures,
        "flags": flags,
        "notes": notes,
    }


def write_metrics_json(plan, metrics_path: Path, timing: dict) -> Path:
    solver = plan.solverOptions.get("solver", plan.defaultSolver)
    if solver == "default":
        solver = "MOSEK" if _mosek_available() else "HiGHS"

    schema = "roost.metrics.v1"

    diagnostics = diagnostics_from_plan(plan)
    run_status = classify_run_status_from_plan(plan, diagnostics=diagnostics)

    if run_status["status"] == "solved":
        metrics = metrics_from_plan(plan)
        complexity = complexity_from_plan(plan)
    else:
        metrics = {}
        complexity = {}

    complexity = complexity_from_plan(plan)

    output_json = {
        "schema": schema,
        "run_status": run_status,
        "timing": timing,
        "solver": solver,
        "metrics": metrics,
        "complexity": complexity,
        "diagnostics": diagnostics,
    }

    with open(metrics_path, "w") as f:
        json.dump(output_json, f, indent=2, sort_keys=True)

    return metrics_path
