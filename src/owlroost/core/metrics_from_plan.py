import json
from datetime import datetime
from pathlib import Path

import numpy as np


def _mosek_available():
    import importlib.util
    import os

    return (
        importlib.util.find_spec("mosek") is not None
        and os.environ.get("MOSEKLM_LICENSE_FILE") is not None
    )


def normalize_timestamp(ts) -> str:
    if isinstance(ts, datetime):
        return ts.isoformat()
    if isinstance(ts, str):
        return ts
    raise TypeError(f"Unsupported timestamp type: {type(ts)}")


# =========================================================
# RUN STATUS
# =========================================================
def classify_run_status_from_plan(plan) -> dict:
    case_status = (plan.caseStatus or "").lower()

    if case_status == "solved":
        return {
            "status": "solved",
            "failure_category": None,
            "failure_detail": None,
        }

    return {
        "status": "failed",
        "failure_category": "unknown",
        "failure_detail": case_status,
    }


# =========================================================
# METRICS
# =========================================================
def financials_from_plan(plan, N=None) -> dict:
    if N is None:
        N = plan.N_n
    if not (0 < N <= plan.N_n):
        raise ValueError(f"Value N={N} is out of range")

    gamma = plan.gamma_n[:N]

    start_year = int(plan.year_n[0])
    final_year = int(plan.year_n[-1])

    identity = {
        "plan_name": plan._name,
        "run_timestamp": normalize_timestamp(plan._timestamp),
        "plan_start_date": str(plan.startDate),
        "year_start": start_year,
        "year_final_bequest": final_year,
        "num_decision_variables": int(plan.A.nvars),
        "num_constraints": int(plan.A.ncons),
    }

    inflation = {
        "final_factor": float(plan.gamma_n[-1]),
    }

    spending = {
        "year0": {
            "future": float(plan.g_n[0]),
            "today": float(plan.g_n[0] / plan.gamma_n[0]),
        },
        "total": {
            "future": float(np.sum(plan.g_n[:N])),
            "today": float(np.sum(plan.g_n[:N] / gamma)),
        },
    }

    roth = {
        "total": {
            "future": float(np.sum(plan.x_in[:, :N])),
            "today": float(np.sum(np.sum(plan.x_in[:, :N], axis=0) / gamma)),
        }
    }

    taxes = {
        "total": {
            "future": float(np.sum(plan.T_n[:N])),
            "today": float(np.sum(plan.T_n[:N] / gamma)),
        }
    }

    estate = np.sum(plan.b_ijn[:, :, plan.N_n], axis=0).copy()
    estate[1] *= 1 - plan.nu
    estate[3] *= 1 - plan.nu

    savings_estate = np.sum(estate)
    debts = plan.remaining_debt_balance

    bequest_future = savings_estate - debts + plan.fixed_assets_bequest_value
    bequest_today = bequest_future / plan.gamma_n[-1]

    bequest = {
        "total": {
            "future": float(bequest_future),
            "today": float(bequest_today),
        }
    }

    spending_future = plan.g_n[:N]
    spending_today = spending_future / gamma

    tax_future = plan.T_n[:N]
    tax_today = tax_future / gamma

    roth_future = np.sum(plan.x_in[:, :N], axis=0)
    roth_today = roth_future / gamma

    assets_future = np.sum(plan.b_ijn[:, :, :N], axis=(0, 1))
    assets_today = assets_future / gamma

    timeseries = {
        "spending": {
            "future_by_year": spending_future.tolist(),
            "today_by_year": spending_today.tolist(),
        },
        "taxes": {
            "future_by_year": tax_future.tolist(),
            "today_by_year": tax_today.tolist(),
        },
        "roth": {
            "future_by_year": roth_future.tolist(),
            "today_by_year": roth_today.tolist(),
        },
        "assets": {
            "future_by_year": assets_future.tolist(),
            "today_by_year": assets_today.tolist(),
        },
        "inflation": {
            "factor_by_year": gamma.tolist(),
        },
    }

    return {
        "identity": identity,
        "inflation": inflation,
        "spending": spending,
        "roth": roth,
        "taxes": taxes,
        "bequest": bequest,
        "timeseries": timeseries,
    }


# =========================================================
# COMPLEXITY
# =========================================================
def complexity_from_plan(plan) -> dict:
    A = plan.A
    B = plan.B

    nvars = int(A.nvars)
    ncons = int(A.ncons)

    nnz = sum(len(row) for row in A.Aind)
    density = nnz / (nvars * ncons) if nvars and ncons else None

    try:
        num_integer_vars = len(B.integralityList())
    except Exception:
        num_integer_vars = None

    year_start = int(plan.year_n[0])
    year_final = int(plan.year_n[-1])
    horizon = year_final - year_start

    nnz_per_var = nnz / nvars if nvars else None
    nnz_per_cons = nnz / ncons if ncons else None
    int_ratio = num_integer_vars / nvars if (num_integer_vars and nvars) else None

    return {
        "num_decision_variables": nvars,
        "num_constraints": ncons,
        "num_nonzeros": int(nnz),
        "matrix_density": float(density) if density else None,
        "num_integer_variables": int(num_integer_vars) if num_integer_vars else None,
        "integer_variable_ratio": float(int_ratio) if int_ratio else None,
        "horizon": int(horizon),
        "nnz_per_variable": float(nnz_per_var) if nnz_per_var else None,
        "nnz_per_constraint": float(nnz_per_cons) if nnz_per_cons else None,
    }


# =========================================================
# RISK - SCENARIO
# =========================================================
def scenario_risk_from_plan(plan) -> dict:
    tau = plan.tau_kn

    stock = np.asarray(tau[0], dtype=float)
    inflation = np.asarray(tau[3], dtype=float)

    if stock.size == 0 or inflation.size == 0:
        return {"valid": False, "reason": "empty return series"}

    N = min(len(stock), len(inflation))
    stock = stock[:N]
    inflation = inflation[:N]

    avg_return = float(np.mean(stock))
    min_return = float(np.min(stock))
    max_return = float(np.max(stock))
    std_return = float(np.std(stock))

    first5_avg = float(np.mean(stock[: min(5, N)]))
    first10_avg = float(np.mean(stock[: min(10, N)]))

    growth = np.cumprod(1 + stock)
    worst_drawdown = float(np.min(growth))

    avg_inflation = float(np.mean(inflation))
    max_inflation = float(np.max(inflation))

    real_returns = (1 + stock) / (1 + inflation) - 1
    avg_real_return = float(np.mean(real_returns))

    real_growth = np.cumprod(1 + real_returns)
    min_real_growth = float(np.min(real_growth))

    flags = []

    if first5_avg < 0:
        flags.append("negative_early_sequence")

    if first10_avg < avg_return:
        flags.append("weak_start_relative_to_average")

    if worst_drawdown < 0.7:
        flags.append("deep_drawdown")

    if worst_drawdown < 0.5:
        flags.append("severe_drawdown")

    if avg_return < 0.02:
        flags.append("low_return_environment")

    if std_return > 0.18:
        flags.append("high_volatility")

    if avg_inflation > 0.035:
        flags.append("high_inflation")

    if max_inflation > 0.06:
        flags.append("inflation_spike")

    if avg_real_return < 0:
        flags.append("negative_real_return_environment")

    if min_real_growth < 0.7:
        flags.append("real_wealth_erosion")

    if "negative_early_sequence" in flags and "high_inflation" in flags:
        scenario_type = "stagflation_sequence"
    elif "negative_early_sequence" in flags:
        scenario_type = "bad_sequence"
    elif "high_inflation" in flags:
        scenario_type = "inflation_stress"
    elif "low_return_environment" in flags:
        scenario_type = "low_return"
    else:
        scenario_type = "baseline"

    # ✅ NORMALIZED SEVERITY
    severity = 0.0
    severity += min(1.0, max(0.0, -first5_avg / 0.10))
    severity += min(1.0, max(0.0, (0.05 - avg_return) / 0.05))
    severity += min(1.0, max(0.0, (avg_inflation - 0.02) / 0.04))
    severity += min(1.0, max(0.0, (0.7 - worst_drawdown) / 0.7))
    severity = float(min(1.0, severity / 4.0))

    return {
        "valid": True,
        "horizon": int(N),
        "returns": {
            "avg": avg_return,
            "min": min_return,
            "max": max_return,
            "std": std_return,
            "first5_avg": first5_avg,
            "first10_avg": first10_avg,
        },
        "drawdown": {"worst_growth_factor": worst_drawdown},
        "inflation": {"avg": avg_inflation, "max": max_inflation},
        "real": {
            "avg_return": avg_real_return,
            "min_growth_factor": min_real_growth,
        },
        "classification": {"scenario_type": scenario_type},
        "severity_score": severity,
        "flags": flags,
    }


# =========================================================
# RISK - OUTCOME
# =========================================================
def outcome_risk_from_plan(plan) -> dict:
    try:
        N = int(plan.N_n)
    except Exception as e:
        return {"valid": False, "reason": f"N_error: {str(e)}"}

    assets_future = np.array([float(np.sum(plan.b_ijn[:, :, n])) for n in range(N)], dtype=float)

    gamma = np.asarray(plan.gamma_n[:N], dtype=float)
    assets_today = assets_future / gamma

    spending_today = np.asarray(plan.g_n[:N], dtype=float) / gamma

    min_assets = float(np.min(assets_today))
    max_assets = float(np.max(assets_today))
    final_assets = float(assets_today[-1])
    median_assets = float(np.median(assets_today))

    depleted = bool(min_assets <= 1e-6)

    depletion_year_index = None
    if depleted:
        idx = np.where(assets_today <= 1e-6)[0]
        if len(idx):
            depletion_year_index = int(idx[0])

    years_to_depletion = int(depletion_year_index) if depleted else int(N)

    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = spending_today / assets_today

    valid = ratios[np.isfinite(ratios)]
    max_ratio = float(np.max(valid)) if len(valid) else None
    avg_ratio = float(np.mean(valid)) if len(valid) else None

    fragility_10 = int(np.sum(valid > 0.10)) if len(valid) else None
    fragility_20 = int(np.sum(valid > 0.20)) if len(valid) else None

    running_max = np.maximum.accumulate(assets_today)
    drawdowns = assets_today / running_max
    drawdowns = drawdowns[np.isfinite(drawdowns)]
    worst_drawdown = float(np.min(drawdowns)) if len(drawdowns) else None

    tail = max(5, int(0.25 * N))
    late_assets = assets_today[-tail:]
    late_running_max = np.maximum.accumulate(late_assets)
    late_dd = late_assets / late_running_max
    late_dd = late_dd[np.isfinite(late_dd)]
    late_drawdown = float(np.min(late_dd)) if len(late_dd) else None

    # ✅ NEW METRICS
    terminal_ratio = None
    if final_assets > 0:
        terminal_ratio = float(spending_today[-1] / final_assets)

    min_cushion = None
    if max_assets > 0:
        min_cushion = float(min_assets / max_assets)

    consumption_ratio = None
    if spending_today[0] > 0:
        consumption_ratio = float(spending_today[-1] / spending_today[0])

    flags = []

    if depleted:
        flags.append("depleted")
    if worst_drawdown is not None and worst_drawdown < 0.5:
        flags.append("severe_asset_drawdown")
    if max_ratio is not None and max_ratio > 0.10:
        flags.append("high_spending_pressure")
    if max_assets > 0 and final_assets < 0.25 * max_assets:
        flags.append("ending_asset_erosion")

    if depleted:
        risk_level = "failure"
    elif worst_drawdown is not None and worst_drawdown < 0.6:
        risk_level = "high"
    elif max_ratio is not None and max_ratio > 0.08:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return {
        "valid": True,
        "horizon": int(N),
        "assets": {
            "min_today": min_assets,
            "median_today": median_assets,
            "max_today": max_assets,
            "final_today": final_assets,
        },
        "depletion": {
            "depleted": depleted,
            "first_depletion_index": depletion_year_index,
            "years_to_depletion": years_to_depletion,
        },
        "sustainability": {
            "max_spending_to_assets_ratio": max_ratio,
            "avg_spending_to_assets_ratio": avg_ratio,
        },
        "fragility": {
            "years_ratio_above_10pct": fragility_10,
            "years_ratio_above_20pct": fragility_20,
        },
        "drawdown": {
            "worst_drawdown_factor": worst_drawdown,
            "lifecycle_drawdown_factor": worst_drawdown,
            "late_life_drawdown_factor": late_drawdown,
        },
        "terminal": {
            "spending_to_assets_ratio": terminal_ratio,
        },
        "cushion": {
            "min_cushion_ratio": min_cushion,
        },
        "consumption": {
            "final_to_initial_ratio": consumption_ratio,
        },
        "classification": {"risk_level": risk_level},
        "flags": flags,
    }


# =========================================================
# RISK WRAPPER
# =========================================================
def risk_from_plan(plan) -> dict:
    try:
        scenario = scenario_risk_from_plan(plan)
    except Exception as e:
        scenario = {"valid": False, "reason": str(e)}

    if (plan.caseStatus or "").lower() == "solved":
        outcome = outcome_risk_from_plan(plan)
    else:
        outcome = {"valid": False, "reason": "plan_not_solved"}

    return {"scenario": scenario, "outcome": outcome}


# =========================================================
# SCORING
# =========================================================
def score_trial(metrics: dict) -> dict:
    outcome = metrics.get("risk", {}).get("outcome", {})

    if not outcome.get("valid"):
        return {"score": -1.0}

    assets = outcome["assets"]
    sustainability = outcome["sustainability"]
    drawdown = outcome["drawdown"]
    fragility = outcome["fragility"]

    final_assets = assets.get("final_today", 0)
    median_assets = assets.get("median_today", 0)
    worst_dd = drawdown.get("worst_drawdown_factor", 0)
    max_ratio = sustainability.get("max_spending_to_assets_ratio", 1)

    fragility_penalty = (fragility.get("years_ratio_above_10pct", 0) or 0) * 0.02 + (
        fragility.get("years_ratio_above_20pct", 0) or 0
    ) * 0.05

    wealth_score = np.log1p(max(final_assets, 0)) / 15
    stability_score = worst_dd if worst_dd is not None else 0
    sustainability_score = max(0, 1 - (max_ratio or 1))
    median_score = median_assets / (median_assets + 1_000_000)

    score = (
        0.4 * wealth_score + 0.2 * stability_score + 0.2 * sustainability_score + 0.2 * median_score
    )

    score -= fragility_penalty

    score = float(max(0.0, min(1.0, score)))

    return {"score": score}


# =========================================================
# WRITE JSON
# =========================================================
def write_metrics_json(plan, metrics_path: Path, timing: dict) -> Path:
    solver = plan.solverOptions.get("solver", plan.defaultSolver)
    if solver == "default":
        solver = "MOSEK" if _mosek_available() else "HiGHS"

    schema = "roost.metrics.v2"

    run_status = classify_run_status_from_plan(plan)
    risk = risk_from_plan(plan)

    if run_status["status"] == "solved":
        financial = financials_from_plan(plan)
    else:
        financial = {}

    complexity = complexity_from_plan(plan)

    score = score_trial({"risk": risk, "financial": financial})

    output_json = {
        "schema": schema,
        "run_status": run_status,
        "timing": timing,
        "solver": solver,
        "financial": financial,
        "risk": risk,
        "complexity": complexity,
        "score": score,
    }

    with open(metrics_path, "w") as f:
        json.dump(output_json, f, indent=2, sort_keys=True)

    return metrics_path
