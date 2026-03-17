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


def write_metrics_json(plan, metrics_path: Path, timing: dict) -> Path:
    solver = plan.solverOptions.get("solver", plan.defaultSolver)
    if solver == "default":
        solver = "MOSEK" if _mosek_available() else "HiGHS"

    schema = "roost.metrics.v1"

    metrics = metrics_from_plan(plan)
    complexity = complexity_from_plan(plan)

    output_json = {
        "schema": schema,
        "metrics": metrics,
        "complexity": complexity,
        "timing": timing,
        "solver": solver,
    }

    with open(metrics_path, "w") as f:
        json.dump(output_json, f, indent=2, sort_keys=True)

    return metrics_path
