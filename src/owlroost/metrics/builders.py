# src/owlroost/metrics/builders.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
from loguru import logger

SCHEMA_VERSION = "roost.metrics.v1"


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


def normalize_failure(run_status: dict) -> dict:
    detail = (run_status.get("failure_detail") or "").lower()

    # Ensure subtype exists
    run_status.setdefault("failure_subtype", None)

    # --------------------------------------------------
    # Solver crash (native / memory)
    # --------------------------------------------------
    if "double free" in detail or "corruption" in detail:
        return {
            "status": "failed",
            "failure_category": "solver_crash",
            "failure_subtype": "memory_corruption",
            "failure_detail": "solver crashed (memory corruption)",
        }

    # --------------------------------------------------
    # Pass-through for worker-level classifications
    # --------------------------------------------------
    if run_status.get("failure_category") in {
        "worker_crash",
        "input_error",
        "hard_crash",
        "empty_output",
        "invalid_output",
        "timeout",
    }:
        return run_status

    return run_status


# =========================================================
# RUN STATUS
# =========================================================
def classify_run_status_from_plan(plan) -> dict:
    case_status_raw = plan.caseStatus or ""
    case_status = case_status_raw.lower().strip()

    # --------------------------------------------------
    # SOLVED
    # --------------------------------------------------
    if case_status == "solved":
        return {
            "status": "solved",
            "failure_category": None,
            "failure_subtype": None,
            "failure_detail": None,
        }

    # --------------------------------------------------
    # Known OWL statuses
    # --------------------------------------------------

    # No feasible / infeasible
    if "no feasible" in case_status or "infeasible" in case_status:
        return {
            "status": "failed",
            "failure_category": "no_feasible_solution",
            "failure_subtype": "infeasible",
            "failure_detail": "no feasible solution",
        }

    # Solver timeout
    if "timeout" in case_status:
        return {
            "status": "failed",
            "failure_category": "timeout",
            "failure_subtype": "solver_timeout",
            "failure_detail": "solver timeout",
        }

    # --------------------------------------------------
    # Unknown / fallback
    # --------------------------------------------------
    # Preserve original text (not lowercased) for readability
    detail = case_status_raw.strip()
    if not detail:
        detail = "unknown"

    return {
        "status": "failed",
        "failure_category": "unknown",
        "failure_subtype": None,
        "failure_detail": detail[:120],  # truncate noise
    }


def ensure_complete_metrics(metrics: dict, status: str) -> dict:
    """
    Non-destructive normalization:
    - Preserves computed values
    - Only fills missing keys
    - Forces defaults only for non-solved runs
    """

    # --------------------------------------------------
    # Top-level structure
    # --------------------------------------------------
    metrics.setdefault("financial", {})
    metrics.setdefault("risk", {})
    metrics.setdefault("run_status", {})
    metrics.setdefault("rates", {})

    risk = metrics.setdefault("risk", {})
    risk_summary = risk.setdefault("summary", {})

    for k in [
        "overall_risk",
        "scenario_severity",
        "depleted",
        "worst_drawdown",
        "terminal_ratio",
        "flag_count",
    ]:
        if k not in risk_summary:
            risk_summary[k] = None

    if "flags" not in risk_summary:
        risk_summary["flags"] = []

    # --------------------------------------------------
    # Financial structure
    # --------------------------------------------------
    fin = metrics["financial"]

    fin.setdefault("baseline", {})
    if "annual_spending" not in fin["baseline"]:
        fin["baseline"]["annual_spending"] = None

    ts = fin.setdefault("timeseries", {})
    spending = ts.setdefault("spending", {})
    ratio = spending.setdefault("ratio", {})

    # --------------------------------------------------
    # Horizon detection
    # --------------------------------------------------
    horizon = (
        metrics.get("financial", {}).get("horizon", {}).get("years")
        or len(ratio.get("by_year", []))
        or metrics.get("risk", {}).get("scenario", {}).get("horizon")
        or metrics.get("complexity", {}).get("horizon")
        or 30
    )

    try:
        horizon = int(horizon)
    except Exception:
        horizon = 30

    fin.setdefault("inflation", {})
    if "final_factor" not in fin["inflation"]:
        fin["inflation"]["final_factor"] = 1.0

    ts = fin.setdefault("timeseries", {})
    ts.setdefault("inflation", {})
    if "factor_by_year" not in ts["inflation"]:
        ts["inflation"]["factor_by_year"] = [1.0] * horizon

    assets = ts.setdefault("assets", {})

    if "today_by_year" not in assets:
        assets["today_by_year"] = [0.0] * horizon

    if "future_by_year" not in assets:
        assets["future_by_year"] = [0.0] * horizon

    spending_ts = ts.setdefault("spending", {})

    if "today_by_year" not in spending_ts:
        spending_ts["today_by_year"] = [0.0] * horizon

    if "future_by_year" not in spending_ts:
        spending_ts["future_by_year"] = [0.0] * horizon

    # --------------------------------------------------
    # Ensure ratio.by_year
    # --------------------------------------------------
    if "by_year" not in ratio or not isinstance(ratio["by_year"], list):
        ratio["by_year"] = [0.0] * horizon if status != "solved" else [None] * horizon

    # --------------------------------------------------
    # Ratio aggregates (NON-DESTRUCTIVE)
    # --------------------------------------------------
    if status != "solved":
        ratio["min"] = 0.0
        ratio["mean"] = 0.0
        ratio["median"] = 0.0
    else:
        values = [v for v in ratio["by_year"] if isinstance(v, (int, float))]
        if values:
            if "min" not in ratio:
                ratio["min"] = min(values)
            if "mean" not in ratio:
                ratio["mean"] = sum(values) / len(values)
            if "median" not in ratio:
                ratio["median"] = sorted(values)[len(values) // 2]
        else:
            for k in ["min", "mean", "median"]:
                if k not in ratio:
                    ratio[k] = None

    # --------------------------------------------------
    # Clamp ratios (safe)
    # --------------------------------------------------
    if isinstance(ratio.get("by_year"), list):
        ratio["by_year"] = [
            min(max(v, 0.0), 2.0) if isinstance(v, (int, float)) else v for v in ratio["by_year"]
        ]

    for k in ["min", "mean", "median"]:
        if isinstance(ratio.get(k), (int, float)):
            ratio[k] = min(max(ratio[k], 0.0), 2.0)

    # --------------------------------------------------
    # Baseline fallback
    # --------------------------------------------------
    if fin["baseline"].get("annual_spending") is None:
        try:
            fin["baseline"]["annual_spending"] = metrics["financial"]["spending"]["year0"]["today"]
        except Exception:
            pass

    # --------------------------------------------------
    # Valid flag
    # --------------------------------------------------
    fin["valid"] = status == "solved"

    # --------------------------------------------------
    # Spending summary (NON-DESTRUCTIVE)
    # --------------------------------------------------
    fin.setdefault("spending_summary", {})
    spending_summary = fin["spending_summary"]

    if status != "solved":
        # overwrite is OK here (failed runs)
        spending_summary.update(
            {
                "min_ratio": 0.0,
                "mean_ratio": 0.0,
                "median_ratio": 0.0,
                "p10_ratio": 0.0,
                "std_ratio": 0.0,
                "years_under_target": horizon,
                "shortfall": 1.0,
                "required_slack": 1.0,
                "min_ratio_to_essential": 0.0,
                "mean_ratio_to_essential": 0.0,
                "median_ratio_to_essential": 0.0,
                "years_below_essential": horizon,
                "essential_spending_breach": 1,
                "min_ratio_to_lifestyle": 0.0,
                "mean_ratio_to_lifestyle": 0.0,
                "median_ratio_to_lifestyle": 0.0,
                "years_below_lifestyle": horizon,
                "consecutive_years_below_lifestyle": horizon,
                "consecutive_years_below_essential": horizon,
                "years_between_essential_and_target": 0,
                "lifestyle_stress_flag": 1,
            }
        )
    else:
        defaults = {
            "min_ratio": None,
            "mean_ratio": None,
            "median_ratio": None,
            "p10_ratio": None,
            "std_ratio": None,
            "years_under_target": None,
            "shortfall": None,
            "required_slack": None,
            "min_ratio_to_essential": None,
            "mean_ratio_to_essential": None,
            "median_ratio_to_essential": None,
            "years_below_essential": None,
            "essential_spending_breach": None,
            "min_ratio_to_lifestyle": None,
            "mean_ratio_to_lifestyle": None,
            "median_ratio_to_lifestyle": None,
            "years_below_lifestyle": None,
            "consecutive_years_below_lifestyle": None,
            "consecutive_years_below_essential": None,
            "years_between_essential_and_target": None,
            "lifestyle_stress_flag": None,
        }

        for k, v in defaults.items():
            if k not in spending_summary:
                spending_summary[k] = v

    return metrics


# =========================================================
# METRICS
# =========================================================


def financial_core_from_plan(plan, N):
    gamma = plan.gamma_n[:N]

    actual_future = plan.g_n[:N]
    actual_today = actual_future / gamma

    k = min(5, N // 2 if N >= 2 else 1)

    early_avg = float(np.mean(actual_today[:k]))
    late_avg = float(np.mean(actual_today[-k:]))

    year0 = float(actual_today[0])
    yearN = float(actual_today[-1])

    survivor_ratio = None
    if early_avg > 0:
        survivor_ratio = late_avg / early_avg
        survivor_ratio = float(min(max(survivor_ratio, 0.0), 2.0))

    spending_profile = {
        "year0": year0,
        "early_avg": early_avg,
        "late_avg": late_avg,
        "yearN": yearN,
        "survivor_ratio": survivor_ratio,
    }

    spending = {
        "year0": {
            "future": float(actual_future[0]),
            "today": float(actual_today[0]),
        },
        "total": {
            "future": float(np.sum(actual_future)),
            "today": float(np.sum(actual_today)),
        },
    }

    taxes = {
        "total": {
            "future": float(np.sum(plan.T_n[:N])),
            "today": float(np.sum(plan.T_n[:N] / gamma)),
        }
    }

    roth = {
        "total": {
            "future": float(np.sum(plan.x_in[:, :N])),
            "today": float(np.sum(np.sum(plan.x_in[:, :N], axis=0) / gamma)),
        }
    }

    # ---- bequest ----
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

    return {
        "spending": spending,
        "spending_profile": spending_profile,
        "taxes": taxes,
        "roth": roth,
        "bequest": bequest,
    }


def spending_metrics_from_plan(plan, N, actual_future, actual_today, gamma, context=None):
    tracer = "starting"
    try:
        # -------------------------------------------------
        # Inputs
        # -------------------------------------------------
        tracer = "1"
        xi = getattr(plan, "xi_n", None)
        if xi is None:
            xi = np.ones_like(actual_future)
        else:
            xi = xi[:N]

        # -------------------------------------------------
        # Baseline (solution-derived, still used for target ratio)
        # -------------------------------------------------
        tracer = "2"

        policy = (context or {}).get("spending_policy", {})
        essential_spending = policy.get("essential_spending")
        lifestyle_spending = policy.get("lifestyle_spending")

        tracer = "3"

        k = policy.get("baseline_years", 3)
        k = max(1, min(k, N))

        if len(actual_future):
            baseline = float(np.mean(actual_future[:k]))
        else:
            baseline = None

        if not isinstance(baseline, (int, float)) or not np.isfinite(baseline) or baseline <= 0:
            fallback = float(actual_today[0]) if len(actual_today) else 1.0
            baseline = fallback if np.isfinite(fallback) and fallback > 0 else 1.0

        # -------------------------------------------------
        # Clean xi
        # -------------------------------------------------
        tracer = "4"
        xi = np.array(xi, dtype=float)
        xi = np.nan_to_num(xi, nan=1.0, posinf=1.0, neginf=1.0)

        # -------------------------------------------------
        # Expected spending
        # -------------------------------------------------
        tracer = "5"
        expected_future = xi * baseline

        lifestyle_future = xi * lifestyle_spending if lifestyle_spending is not None else None
        essential_future = xi * essential_spending if essential_spending is not None else None

        # -------------------------------------------------
        # Ratios
        # -------------------------------------------------
        tracer = "6"
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.divide(
                actual_future,
                expected_future,
                out=np.zeros_like(actual_future),
                where=expected_future > 0,
            )

            ratio_lifestyle = (
                np.divide(
                    actual_future,
                    lifestyle_future,
                    out=np.zeros_like(actual_future),
                    where=lifestyle_future > 0,
                )
                if lifestyle_future is not None
                else None
            )

            ratio_essential = (
                np.divide(
                    actual_future,
                    essential_future,
                    out=np.zeros_like(actual_future),
                    where=essential_future > 0,
                )
                if essential_future is not None
                else None
            )

        # Clip for stability
        ratio = np.clip(ratio, 0.0, 2.0)

        if ratio_lifestyle is not None:
            ratio_lifestyle = np.clip(ratio_lifestyle, 0.0, 2.0)

        if ratio_essential is not None:
            ratio_essential = np.clip(ratio_essential, 0.0, 2.0)

        clean = ratio[np.isfinite(ratio)]

        clean_lifestyle = (
            ratio_lifestyle[np.isfinite(ratio_lifestyle)] if ratio_lifestyle is not None else []
        )

        clean_essential = (
            ratio_essential[np.isfinite(ratio_essential)] if ratio_essential is not None else []
        )

        # -------------------------------------------------
        # Helpers
        # -------------------------------------------------
        tracer = "7"

        def safe_stats(arr):
            if len(arr):
                return float(np.min(arr)), float(np.mean(arr)), float(np.median(arr))
            return None, None, None

        def max_consecutive_below(arr):
            max_run = run = 0
            for v in arr:
                if v < 1.0:
                    run += 1
                    max_run = max(max_run, run)
                else:
                    run = 0
            return max_run

        # -------------------------------------------------
        # Summary metrics
        # -------------------------------------------------
        tracer = "8"

        min_ratio, mean_ratio, median_ratio = safe_stats(clean)

        min_life, mean_life, median_life = safe_stats(clean_lifestyle)
        min_ess, mean_ess, median_ess = safe_stats(clean_essential)

        years_under_target = int(np.sum(clean < 1.0)) if len(clean) else None

        years_below_lifestyle = int(np.sum(clean_lifestyle < 1.0)) if len(clean_lifestyle) else None
        years_below_essential = int(np.sum(clean_essential < 1.0)) if len(clean_essential) else None

        consecutive_below_lifestyle = (
            max_consecutive_below(clean_lifestyle) if len(clean_lifestyle) else None
        )
        consecutive_below_essential = (
            max_consecutive_below(clean_essential) if len(clean_essential) else None
        )

        # -------------------------------------------------
        # Flags (respect None)
        # -------------------------------------------------
        tracer = "9"

        lifestyle_stress_flag = (
            1
            if (years_below_lifestyle is not None and years_below_lifestyle > 0)
            else 0
            if lifestyle_spending is not None
            else None
        )

        essential_spending_breach = (
            1
            if (years_below_essential is not None and years_below_essential > 0)
            else 0
            if essential_spending is not None
            else None
        )

        # -------------------------------------------------
        # Return
        # -------------------------------------------------
        tracer = "10"

        return {
            "baseline_valid": True,
            "baseline": {"annual_spending": float(baseline)},
            "spending_summary": {
                "min_ratio": min_ratio,
                "mean_ratio": mean_ratio,
                "median_ratio": median_ratio,
                "years_under_target": years_under_target,
                "min_ratio_to_lifestyle": min_life,
                "mean_ratio_to_lifestyle": mean_life,
                "median_ratio_to_lifestyle": median_life,
                "min_ratio_to_essential": min_ess,
                "mean_ratio_to_essential": mean_ess,
                "median_ratio_to_essential": median_ess,
                "years_below_lifestyle": years_below_lifestyle,
                "years_below_essential": years_below_essential,
                "consecutive_years_below_lifestyle": consecutive_below_lifestyle,
                "consecutive_years_below_essential": consecutive_below_essential,
                "lifestyle_stress_flag": lifestyle_stress_flag,
                "essential_spending_breach": essential_spending_breach,
            },
            "spending_policy": {
                "essential_spending": float(essential_spending)
                if essential_spending is not None
                else None,
                "lifestyle_spending": float(lifestyle_spending)
                if lifestyle_spending is not None
                else None,
            },
        }

    except Exception as e:
        logger.exception("spending_metrics_from_plan failed")
        return {
            "baseline_valid": False,
            "spending_error_tracer": tracer,
            "spending_error": str(e),
        }


def financials_from_plan(plan, N=None, context=None) -> dict:
    try:
        if not hasattr(plan, "g_n") or not hasattr(plan, "gamma_n"):
            return {"valid": False, "reason": "missing_core_arrays"}

        if N is None:
            N = plan.N_n

        gamma = plan.gamma_n[:N]
        actual_future = plan.g_n[:N]
        actual_today = actual_future / gamma

        assets_future = np.array(
            [float(np.sum(plan.b_ijn[:, :, n])) for n in range(N)], dtype=float
        )

        assets_today = assets_future / gamma

        # --- inflation ---
        inflation = {"final_factor": float(gamma[-1]) if len(gamma) else 1.0}

        inflation_ts = {"factor_by_year": [float(x) for x in gamma]}

        # ---- core (never fails) ----
        core = financial_core_from_plan(plan, N)

        # ---- spending metrics (may fail) ----
        spending = spending_metrics_from_plan(plan, N, actual_future, actual_today, gamma, context)

        result = {
            "valid": True,
            "inflation": inflation,
            **core,
            **spending,
        }

        # --- merge timeseries safely ---
        result.setdefault("timeseries", {})
        result["timeseries"]["inflation"] = inflation_ts

        result["timeseries"]["assets"] = {
            "future_by_year": [float(x) for x in assets_future],
            "today_by_year": [float(x) for x in assets_today],
        }
        result["timeseries"]["spending"] = {
            "future_by_year": [float(x) for x in actual_future],
            "today_by_year": [float(x) for x in actual_today],
        }

        return result

    except Exception as e:
        logger.exception("financials_from_plan failed")
        return {"valid": False, "reason": str(e)}


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

    # Prefer N_n (always available)
    try:
        horizon = int(plan.N_n)
    except Exception:
        horizon = None

    # Fallback if needed
    if not horizon:
        horizon = len(getattr(plan, "g_n", [])) or 30

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
        "horizon": int(len(plan.g_n[:N])),
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

    terminal_ratio = None
    if final_assets > 0:
        terminal_ratio = float(spending_today[-1] / final_assets)

    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = assets_today / spending_today

    valid = ratios[np.isfinite(ratios)]
    min_cushion = float(np.min(valid)) if len(valid) else None

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


def summarize_risk(scenario: dict, outcome: dict) -> dict:
    if not scenario.get("valid") or not outcome.get("valid"):
        return {"valid": False}

    severity = scenario.get("severity_score")
    if isinstance(severity, (int, float)):
        severity = float(min(max(severity, 0.0), 1.0))

    risk_level = outcome.get("classification", {}).get("risk_level")

    depletion = outcome.get("depletion", {}).get("depleted", False)
    worst_dd = outcome.get("drawdown", {}).get("worst_drawdown_factor")
    terminal_ratio = outcome.get("terminal", {}).get("spending_to_assets_ratio")

    flags = set(scenario.get("flags", [])) | set(outcome.get("flags", []))

    # --------------------------------------------------
    # Harmonized (consumption-first) risk classification
    # --------------------------------------------------

    # Priority 1: depletion (true failure)
    if depletion:
        overall = "failure"

    # Priority 2: spending-driven stress (from outcome flags)
    elif "high_spending_pressure" in flags:
        overall = "high"

    # Priority 3: scenario severity (bad environment)
    elif severity is not None and severity > 0.6:
        overall = "high"

    # Priority 4: drawdown (secondary signal, softened)
    elif worst_dd is not None and worst_dd < 0.3:
        overall = "moderate"

    # Priority 5: fallback to outcome classification
    elif risk_level in ("high", "moderate"):
        overall = risk_level

    else:
        overall = "low"

    return {
        "valid": True,
        "overall_risk": overall,
        "scenario_severity": severity,
        "depleted": depletion,
        "worst_drawdown": worst_dd,
        "terminal_ratio": terminal_ratio,
        "flag_count": len(flags),
        "flags": sorted(flags),
    }


# =========================================================
# RISK WRAPPER
# =========================================================
def risk_from_plan(plan) -> dict:
    try:
        scenario = scenario_risk_from_plan(plan)
    except Exception as e:
        scenario = {"valid": False, "reason": str(e)}

    try:
        solved = (plan.caseStatus or "").lower() == "solved"
    except Exception:
        solved = False

    if solved:
        try:
            outcome = outcome_risk_from_plan(plan)
        except Exception as e:
            outcome = {"valid": False, "reason": f"outcome_error: {str(e)}"}
    else:
        outcome = {"valid": False, "reason": "plan_not_solved"}

    overall_risk = "failure" if not outcome.get("valid") else "unknown"

    sev = scenario.get("severity_score")
    if isinstance(sev, (int, float)):
        sev = float(min(max(sev, 0.0), 1.0))

    summary = summarize_risk(scenario, outcome)
    if not summary.get("valid"):
        summary = {
            "valid": False,
            "overall_risk": overall_risk,
            "scenario_severity": sev,
            "depleted": None,
            "worst_drawdown": None,
            "terminal_ratio": None,
            "flag_count": None,
            "flags": [],
        }

    return {
        "scenario": scenario,
        "outcome": outcome,
        "summary": summary,
    }


def social_security_from_plan(plan) -> dict:
    try:
        # --------------------------------------------
        # Mode (raw from plan)
        # --------------------------------------------
        optimized = plan._ssa_lp

        # --------------------------------------------
        # Optimized ages (actual result)
        # --------------------------------------------
        optimized_ages = None
        if hasattr(plan, "ssecAges") and plan.ssecAges is not None:
            try:
                optimized_ages = [float(x) for x in plan.ssecAges]
            except Exception:
                optimized_ages = None

        # --------------------------------------------
        # Return
        # --------------------------------------------
        return {
            "optimized": optimized,
            "ages": optimized_ages,
        }

    except Exception:
        return {
            "optimized": None,
            "ages": None,
        }


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
# RATES
# =========================================================


def rates_from_plan(plan) -> dict:
    try:
        tau = plan.tau_kn

        stock = np.asarray(tau[0], dtype=float)
        bonds = np.asarray(tau[2], dtype=float)
        inflation = np.asarray(tau[3], dtype=float)

        if stock.size == 0 or inflation.size == 0:
            return {"valid": False, "reason": "empty rates"}

        N = min(len(stock), len(inflation))
        stock = stock[:N]
        bonds = bonds[:N]
        inflation = inflation[:N]

        # --------------------------------------------------
        # Real returns
        # --------------------------------------------------
        real = (1 + stock) / (1 + inflation) - 1

        # --------------------------------------------------
        # Helpers
        # --------------------------------------------------
        def stats(arr):
            return {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
            }

        def geom_mean(arr):
            return float(np.prod(1 + arr) ** (1 / len(arr)) - 1)

        # --------------------------------------------------
        # Early regime (7-year default)
        # --------------------------------------------------
        k = min(7, N)

        early_real = real[:k]

        early = {
            "years": int(k),
            "real_mean": float(np.mean(early_real)),
            "real_cagr": geom_mean(early_real),
            "min_year": float(np.min(early_real)),
        }

        # --------------------------------------------------
        # Return
        # --------------------------------------------------
        return {
            "valid": True,
            "returns": stats(stock),
            "bonds": stats(bonds),
            "inflation": stats(inflation),
            "real": stats(real),
            "early": early,
        }

    except Exception as e:
        logger.exception("rates_from_plan failed")
        return {"valid": False, "reason": str(e)}


# =========================================================
# WRITE JSON
# =========================================================
def write_metrics_json(
    plan, metrics_path: Path, timing: dict, failure_override=None, context=None
) -> Path:
    def safe_compute(fn):
        try:
            return fn()
        except Exception as e:
            return {"valid": False, "reason": f"{fn.__name__}_error: {str(e)}"}

    try:
        solver_opts = getattr(plan, "solverOptions", {})
        default_solver = getattr(plan, "defaultSolver", "unknown")

        solver = solver_opts.get("solver", default_solver)
        if solver == "default":
            solver = "MOSEK" if _mosek_available() else "HiGHS"

        identity = {
            "plan_name": (context or {}).get("case_name") or getattr(plan, "_name", "unknown")
        }

        try:
            horizon = int(plan.N_n)
        except Exception:
            horizon = None

        def build_run_status(plan, failure_override):
            if failure_override:
                return normalize_failure(failure_override)
            return normalize_failure(classify_run_status_from_plan(plan))

        run_status = build_run_status(plan, failure_override)

        if run_status.get("failure_detail"):
            run_status["failure_detail"] = run_status["failure_detail"].split("\n")[0][:120]

        is_solved = run_status.get("status") == "solved"

        if is_solved:
            financial = safe_compute(lambda: financials_from_plan(plan, context=context))
            risk = safe_compute(lambda: risk_from_plan(plan))
            complexity = safe_compute(lambda: complexity_from_plan(plan))
            social_security = safe_compute(lambda: social_security_from_plan(plan))
            rates = safe_compute(lambda: rates_from_plan(plan))

            if financial.get("valid") is True and risk.get("summary", {}).get("valid") is not False:
                score = score_trial({"risk": risk, "financial": financial})
            else:
                score = {"score": None}

        else:
            financial = {}
            risk = {}
            complexity = {}
            social_security = {}
            rates = {}
            score = {"score": None}

        output_json = {
            "schema": SCHEMA_VERSION,
            "identity": identity,
            "run_status": run_status,
            "horizon": {"years": horizon},
            "timing": timing,
            "solver": solver,
            "financial": financial,
            "risk": risk,
            "complexity": complexity,
            "social_security": social_security,
            "rates": rates,
            "score": score,
        }

    except Exception as e:
        output_json = {
            "schema": SCHEMA_VERSION,
            "run_status": {
                "status": "failed",
                "failure_category": "metrics_error",
                "failure_detail": str(e),
            },
            "timing": timing,
            "financial": {},
            "risk": {},
            "rates": {},
            "complexity": {},
        }

    # --------------------------------------------------
    # 🔥 NORMALIZE STRUCTURE HERE (CRITICAL)
    # --------------------------------------------------
    run_status_obj = output_json.get("run_status", {})
    status = run_status_obj.get("status", "unknown")

    output_json = ensure_complete_metrics(output_json, status)

    if status != "solved":
        fin = output_json.setdefault("financial", {})

        fin["valid"] = False

        ts = fin.setdefault("timeseries", {})
        spending = ts.setdefault("spending", {})
        ratio = spending.setdefault("ratio", {})

        # Ensure safe defaults
        ratio.setdefault("by_year", [])
        ratio.setdefault("min", 0.0)
        ratio.setdefault("mean", 0.0)
        ratio.setdefault("median", 0.0)

    with open(metrics_path, "w") as f:
        json.dump(output_json, f, indent=2, sort_keys=True)

    return metrics_path
