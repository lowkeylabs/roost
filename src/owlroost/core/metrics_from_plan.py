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


def normalize_failure(run_status: dict) -> dict:
    detail = (run_status.get("failure_detail") or "").lower()

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
    # Worker crash (subprocess died)
    # --------------------------------------------------
    if run_status.get("failure_category") == "worker_crash":
        return {
            "status": "failed",
            "failure_category": "worker_crash",
            "failure_detail": "worker process crashed",
        }

    return run_status


# =========================================================
# RUN STATUS
# =========================================================
def classify_run_status_from_plan(plan) -> dict:
    case_status = (plan.caseStatus or "").lower()

    # --------------------------------------------------
    # SOLVED
    # --------------------------------------------------
    if case_status == "solved":
        return {
            "status": "solved",
            "failure_category": None,
            "failure_detail": None,
        }

    # --------------------------------------------------
    # Known OWL statuses
    # --------------------------------------------------
    if "no feasible" in case_status:
        return {
            "status": "failed",
            "failure_category": "no_feasible_solution",
            "failure_detail": "no feasible solution",
        }

    if "infeasible" in case_status:
        return {
            "status": "failed",
            "failure_category": "no_feasible_solution",
            "failure_detail": "infeasible",
        }

    if "timeout" in case_status:
        return {
            "status": "failed",
            "failure_category": "timeout",
            "failure_detail": "solver timeout",
        }

    # --------------------------------------------------
    # Fallback
    # --------------------------------------------------
    return {
        "status": "failed",
        "failure_category": "unknown",
        "failure_detail": case_status[:120],  # truncate noise
    }


def ensure_complete_metrics(metrics: dict, status: str) -> dict:
    """
    Ensures all required metric structure exists across:
    - SOLVED
    - UNSUCCESSFUL
    - FAILED

    Guarantees aggregation-safe structure.
    """

    # --------------------------------------------------
    # Top-level structure
    # --------------------------------------------------
    metrics.setdefault("financial", {})
    metrics.setdefault("risk", {})
    metrics.setdefault("run_status", {})

    # --------------------------------------------------
    # Financial structure
    # --------------------------------------------------
    fin = metrics["financial"]

    fin.setdefault("baseline", {})
    fin["baseline"].setdefault("annual_spending", None)

    ts = fin.setdefault("timeseries", {})
    spending = ts.setdefault("spending", {})
    ratio = spending.setdefault("ratio", {})

    # --------------------------------------------------
    # Determine horizon (needed for by_year)
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

    # --------------------------------------------------
    # CRITICAL: ensure ratio.by_year exists
    # --------------------------------------------------
    if "by_year" not in ratio or not isinstance(ratio["by_year"], list):
        if status != "solved":
            # worst-case fallback
            ratio["by_year"] = [0.0] * horizon
        else:
            # unknown but valid structure
            ratio["by_year"] = [None] * horizon

    # --------------------------------------------------
    # CRITICAL: normalize aggregate ratio values
    # --------------------------------------------------
    if status != "solved":
        ratio["min"] = 0.0
        ratio["mean"] = 0.0
        ratio["median"] = 0.0
    else:
        # derive if missing
        values = [v for v in ratio["by_year"] if isinstance(v, (int, float))]

        if values:
            ratio.setdefault("min", min(values))
            ratio.setdefault("mean", sum(values) / len(values))
            ratio.setdefault(
                "median",
                sorted(values)[len(values) // 2],
            )
        else:
            ratio.setdefault("min", None)
            ratio.setdefault("mean", None)
            ratio.setdefault("median", None)

    # --------------------------------------------------
    # Optional: clamp ratios for stability
    # --------------------------------------------------
    if isinstance(ratio.get("by_year"), list):
        ratio["by_year"] = [
            min(max(v, 0.0), 2.0) if isinstance(v, (int, float)) else v for v in ratio["by_year"]
        ]

    if isinstance(ratio.get("min"), (int, float)):
        ratio["min"] = min(max(ratio["min"], 0.0), 2.0)

    if isinstance(ratio.get("mean"), (int, float)):
        ratio["mean"] = min(max(ratio["mean"], 0.0), 2.0)

    if isinstance(ratio.get("median"), (int, float)):
        ratio["median"] = min(max(ratio["median"], 0.0), 2.0)

    # --------------------------------------------------
    # Baseline fallback (important for display)
    # --------------------------------------------------
    if fin["baseline"].get("annual_spending") is None:
        try:
            fin["baseline"]["annual_spending"] = metrics["financial"]["spending"]["year0"]["today"]
        except Exception:
            pass

    # --------------------------------------------------
    # Mark validity
    # --------------------------------------------------
    fin["valid"] = status == "solved"

    # --------------------------------------------------
    # Ensure spending_summary exists
    # --------------------------------------------------
    fin.setdefault("spending_summary", {})

    summary = fin["spending_summary"]

    if status != "solved":
        summary.update(
            {
                # EXISTING
                "min_ratio": 0.0,
                "mean_ratio": 0.0,
                "median_ratio": 0.0,
                "p10_ratio": 0.0,
                "std_ratio": 0.0,
                "years_under_target": horizon,
                "shortfall": 1.0,
                "required_slack": 1.0,
                # MINIMUM
                "min_ratio_to_minimum": 0.0,
                "mean_ratio_to_minimum": 0.0,
                "median_ratio_to_minimum": 0.0,
                "years_below_minimum": horizon,
                "floor_breach": 1,
                # ACCEPTABLE
                "min_ratio_to_acceptable": 0.0,
                "mean_ratio_to_acceptable": 0.0,
                "median_ratio_to_acceptable": 0.0,
                "years_below_acceptable": horizon,
                "consecutive_years_below_acceptable": horizon,
                "consecutive_years_below_minimum": horizon,
                # DERIVED
                "years_between_min_and_target": 0,
                # FLAGS
                "spending_stress_flag": 1,
            }
        )
    else:
        profile = fin.setdefault("spending_profile", {})

        profile.setdefault("year0", None)
        profile.setdefault("early_avg", None)
        profile.setdefault("late_avg", None)
        profile.setdefault("yearN", None)
        profile.setdefault("survivor_ratio", None)

        summary.setdefault("min_ratio", None)
        summary.setdefault("mean_ratio", None)
        summary.setdefault("median_ratio", None)
        summary.setdefault("p10_ratio", None)
        summary.setdefault("std_ratio", None)
        summary.setdefault("years_under_target", None)
        summary.setdefault("shortfall", None)
        summary.setdefault("required_slack", None)

        summary.setdefault("min_ratio_to_minimum", None)
        summary.setdefault("mean_ratio_to_minimum", None)
        summary.setdefault("median_ratio_to_minimum", None)
        summary.setdefault("years_below_minimum", None)
        summary.setdefault("floor_breach", None)

        summary.setdefault("min_ratio_to_acceptable", None)
        summary.setdefault("mean_ratio_to_acceptable", None)
        summary.setdefault("median_ratio_to_acceptable", None)
        summary.setdefault("years_below_acceptable", None)
        summary.setdefault("consecutive_years_below_acceptable", None)

        summary.setdefault("years_between_min_and_target", None)
        summary.setdefault("spending_stress_flag", None)

    return metrics


# =========================================================
# RUN IDENTITY
# =========================================================


def identity_from_plan(plan) -> dict:
    return {
        "plan_name": getattr(plan, "_name", "unknown"),
    }


# =========================================================
# METRICS
# =========================================================
def financials_from_plan(plan, N=None) -> dict:
    try:
        if not hasattr(plan, "g_n") or not hasattr(plan, "gamma_n"):
            return {"valid": False, "reason": "missing_core_arrays"}

        if N is None:
            N = plan.N_n
        if not (0 < N <= plan.N_n):
            raise ValueError(f"Value N={N} is out of range")

        gamma = plan.gamma_n[:N]

        start_year = int(plan.year_n[0])
        final_year = int(plan.year_n[-1])

        horizon = {
            "start_year": int(start_year),
            "final_year": int(final_year),
            "years": int(len(plan.g_n[:N])),
        }

        inflation = {
            "final_factor": float(plan.gamma_n[-1]),
        }

        # =========================================================
        # SPENDING (ACTUAL = g_n, EXPECTED = xi_n)
        # =========================================================

        actual_future = plan.g_n[:N]
        actual_today = actual_future / gamma
        xi = plan.xi_n[:N]

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

        risk_cfg = getattr(plan, "_config_extra", {}) or {}
        risk_cfg = risk_cfg.get("risk_analysis", {}) or {}

        k = risk_cfg.get("baseline_years", 3)
        k = max(1, min(k, N))  # safe bounds

        baseline = float(np.mean(actual_future[:k])) if len(actual_future) else None

        if baseline is None or baseline == 0:
            return {"valid": False, "reason": "invalid_baseline"}

        # --------------------------------------------------
        # Risk thresholds (from Plan config — no hardcoding)
        # --------------------------------------------------

        minimum_spending = risk_cfg.get("minimum_spending")
        acceptable_spending = risk_cfg.get("acceptable_spending")
        acceptable_ratio = risk_cfg.get("acceptable_spending_ratio_to_minimum")

        # Derive acceptable if needed
        if acceptable_spending is None and acceptable_ratio and minimum_spending:
            acceptable_spending = minimum_spending * acceptable_ratio

        if acceptable_spending is not None and minimum_spending is not None:
            if acceptable_spending < minimum_spending:
                acceptable_spending = minimum_spending

        expected_future = plan.xi_n[:N] * baseline
        expected_today = expected_future / gamma

        shortfall_future = expected_future - actual_future
        shortfall_today = shortfall_future / gamma

        # --------------------------------------------------
        # Ratios relative to minimum and acceptable spending
        # --------------------------------------------------
        if minimum_spending and minimum_spending > 0:
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio_to_minimum = actual_today / minimum_spending
        else:
            ratio_to_minimum = np.full_like(actual_today, np.nan)

        if acceptable_spending and acceptable_spending > 0:
            acceptable_future = xi * acceptable_spending
            acceptable_today = acceptable_future / gamma

            with np.errstate(divide="ignore", invalid="ignore"):
                ratio_to_acceptable = actual_today / acceptable_today
        else:
            acceptable_future = np.full_like(actual_future, np.nan)
            acceptable_today = np.full_like(actual_today, np.nan)
            ratio_to_acceptable = np.full_like(actual_today, np.nan)

        # Clamp for stability (same convention as existing ratios)
        ratio_to_minimum = np.clip(ratio_to_minimum, 0.0, 2.0)
        ratio_to_acceptable = np.clip(ratio_to_acceptable, 0.0, 2.0)

        if (plan.caseStatus or "").lower() != "solved":
            ratio = np.zeros(N)
            shortfall_future = expected_future.copy()
            shortfall_today = expected_today.copy()
            ratio_to_minimum = np.zeros_like(actual_today)
            ratio_to_acceptable = np.zeros_like(actual_today)
        else:
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = np.divide(
                    actual_future,
                    expected_future,
                    out=np.zeros_like(actual_future),
                    where=expected_future > 0,
                )
                ratio = np.clip(ratio, 0.0, 2.0)

        # Summary (keep backward compatibility: "spending" = actual)
        spending = {
            "year0": {
                "future": float(actual_future[0]),
                "today": float(actual_today[0]),
            },
            "baseline": {
                "annual_spending": float(baseline),
            },
            "total": {
                "future": float(np.sum(actual_future)),
                "today": float(np.sum(actual_today)),
            },
        }

        # =========================================================
        # OTHER FINANCIALS (unchanged)
        # =========================================================

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

        tax_future = plan.T_n[:N]
        tax_today = tax_future / gamma

        roth_future = np.sum(plan.x_in[:, :N], axis=0)
        roth_today = roth_future / gamma

        assets_future = np.sum(plan.b_ijn[:, :, :N], axis=(0, 1))
        assets_today = assets_future / gamma

        # =========================================================
        # TIMESERIES (ENHANCED)
        # =========================================================

        timeseries = {
            "spending": {
                "expected": {
                    "future_by_year": expected_future.tolist(),
                    "today_by_year": expected_today.tolist(),
                },
                "actual": {
                    "future_by_year": actual_future.tolist(),
                    "today_by_year": actual_today.tolist(),
                },
                "acceptable": {
                    "future_by_year": acceptable_future.tolist(),
                    "today_by_year": acceptable_today.tolist(),
                },
                "shortfall": {
                    "future_by_year": shortfall_future.tolist(),
                    "today_by_year": shortfall_today.tolist(),
                },
                # NOTE:
                # ratio (target-based) uses future values (OWL-native)
                # ratio_to_minimum / acceptable use today values (behavioral interpretation)
                "ratio": {
                    "by_year": ratio.tolist(),
                    "min": float(np.nanmin(ratio)) if np.isfinite(ratio).any() else None,
                    "mean": float(np.nanmean(ratio)) if np.isfinite(ratio).any() else None,
                    "median": float(np.nanmedian(ratio)) if np.isfinite(ratio).any() else None,
                },
                "ratio_to_minimum": {
                    "by_year": ratio_to_minimum.tolist(),
                    "min": float(np.nanmin(ratio_to_minimum))
                    if np.isfinite(ratio_to_minimum).any()
                    else None,
                    "mean": float(np.nanmean(ratio_to_minimum))
                    if np.isfinite(ratio_to_minimum).any()
                    else None,
                    "median": float(np.nanmedian(ratio_to_minimum))
                    if np.isfinite(ratio_to_minimum).any()
                    else None,
                },
                "ratio_to_acceptable": {
                    "by_year": ratio_to_acceptable.tolist(),
                    "min": float(np.nanmin(ratio_to_acceptable))
                    if np.isfinite(ratio_to_acceptable).any()
                    else None,
                    "mean": float(np.nanmean(ratio_to_acceptable))
                    if np.isfinite(ratio_to_acceptable).any()
                    else None,
                    "median": float(np.nanmedian(ratio_to_acceptable))
                    if np.isfinite(ratio_to_acceptable).any()
                    else None,
                },
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
        # =========================================================
        # SPENDING SUMMARY
        # =========================================================

        clean = ratio[np.isfinite(ratio)]
        clean_min = ratio_to_minimum[np.isfinite(ratio_to_minimum)]
        clean_acc = ratio_to_acceptable[np.isfinite(ratio_to_acceptable)]

        if len(clean):
            years_below_target = int(np.sum(clean < 1.0))
            years_below_minimum = int(np.sum(clean_min < 1.0)) if len(clean_min) else None
            years_below_acceptable = int(np.sum(clean_acc < 1.0)) if len(clean_acc) else None

            def max_consecutive_below(arr, threshold):
                max_run = run = 0
                for v in arr:
                    if v < threshold:
                        run += 1
                        max_run = max(max_run, run)
                    else:
                        run = 0
                return max_run

            consecutive_below_acceptable = (
                max_consecutive_below(clean_acc, 1.0) if len(clean_acc) else None
            )

            consecutive_below_minimum = (
                max_consecutive_below(clean_min, 1.0) if len(clean_min) else None
            )

            spending_summary = {
                # ---------------------------------------
                # EXISTING (UNCHANGED)
                # ---------------------------------------
                "min_ratio": float(np.min(clean)),
                "mean_ratio": float(np.mean(clean)),
                "median_ratio": float(np.median(clean)),
                "p10_ratio": float(np.percentile(clean, 10)),
                "std_ratio": float(np.std(clean)),
                "years_under_target": years_below_target,
                "shortfall": float(1.0 - np.min(clean)),
                "required_slack": float(1.0 - np.min(clean)),
                # ---------------------------------------
                # MINIMUM (floor)
                # ---------------------------------------
                "min_ratio_to_minimum": float(np.min(clean_min)) if len(clean_min) else None,
                "mean_ratio_to_minimum": float(np.mean(clean_min)) if len(clean_min) else None,
                "median_ratio_to_minimum": float(np.median(clean_min)) if len(clean_min) else None,
                "years_below_minimum": years_below_minimum,
                "consecutive_years_below_minimum": consecutive_below_minimum,
                "floor_breach": int(np.any(clean_min < 1.0)) if len(clean_min) else 0,
                # ---------------------------------------
                # ACCEPTABLE (behavioral)
                # ---------------------------------------
                "min_ratio_to_acceptable": float(np.min(clean_acc)) if len(clean_acc) else None,
                "mean_ratio_to_acceptable": float(np.mean(clean_acc)) if len(clean_acc) else None,
                "median_ratio_to_acceptable": float(np.median(clean_acc))
                if len(clean_acc)
                else None,
                "years_below_acceptable": years_below_acceptable,
                "consecutive_years_below_acceptable": consecutive_below_acceptable,
                # ---------------------------------------
                # DERIVED RELATIONSHIP
                # ---------------------------------------
                "years_between_min_and_target": (
                    max(0, years_below_target - years_below_minimum)
                    if years_below_target is not None and years_below_minimum is not None
                    else None
                ),
                # ---------------------------------------
                # STRESS FLAG (neutral naming)
                # ---------------------------------------
                "spending_stress_flag": int(np.any(clean_acc < 1.0)) if len(clean_acc) else 0,
            }

        else:
            spending_summary = {
                "min_ratio": None,
                "mean_ratio": None,
                "median_ratio": None,
                "p10_ratio": None,
                "std_ratio": None,
                "years_under_target": None,
                "shortfall": None,
                "required_slack": None,
                "min_ratio_to_minimum": None,
                "mean_ratio_to_minimum": None,
                "median_ratio_to_minimum": None,
                "years_below_minimum": None,
                "consecutive_years_below_minimum": None,
                "min_ratio_to_acceptable": None,
                "mean_ratio_to_acceptable": None,
                "median_ratio_to_acceptable": None,
                "years_below_acceptable": None,
                "consecutive_years_below_acceptable": None,
                "years_between_min_and_target": None,
                "spending_stress_flag": None,
            }

    except Exception as e:
        return {
            "valid": False,
            "reason": f"financials_error: {str(e)}",
        }

    return {
        "horizon": horizon,
        "inflation": inflation,
        "spending": spending,  # actual (unchanged behavior)
        "spending_profile": spending_profile,
        "roth": roth,
        "taxes": taxes,
        "bequest": bequest,
        "timeseries": timeseries,
        "spending_summary": spending_summary,
        "risk_analysis": {
            "minimum_spending": float(minimum_spending) if minimum_spending else None,
            "acceptable_spending": float(acceptable_spending) if acceptable_spending else None,
            "acceptable_spending_ratio_to_minimum": acceptable_ratio,
        },
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
    def safe_call(fn, default):
        try:
            return fn(plan)
        except Exception as e:
            return {"valid": False, "reason": f"{fn.__name__}_error: {str(e)}"}

    try:
        solver_opts = getattr(plan, "solverOptions", {})
        default_solver = getattr(plan, "defaultSolver", "unknown")

        solver = solver_opts.get("solver", default_solver)
        if solver == "default":
            solver = "MOSEK" if _mosek_available() else "HiGHS"

        schema = "roost.metrics.v2"

        identity = identity_from_plan(plan)
        raw_status = classify_run_status_from_plan(plan)
        run_status = normalize_failure(raw_status)
        if run_status.get("failure_detail"):
            run_status["failure_detail"] = run_status["failure_detail"].split("\n")[0][:120]

        financial = safe_call(financials_from_plan, {})
        risk = safe_call(risk_from_plan, {})
        complexity = safe_call(complexity_from_plan, {})

        score = score_trial({"risk": risk, "financial": financial})

        output_json = {
            "schema": schema,
            "identity": identity,
            "run_status": run_status,
            "timing": timing,
            "solver": solver,
            "financial": financial,
            "risk": risk,
            "complexity": complexity,
            "score": score,
        }

    except Exception as e:
        output_json = {
            "schema": "roost.metrics.v2",
            "run_status": {
                "status": "failed",
                "failure_category": "metrics_error",
                "failure_detail": str(e),
            },
            "timing": timing,
            "financial": {},
            "risk": {},
            "complexity": {},
        }

    # --------------------------------------------------
    # 🔥 NORMALIZE STRUCTURE HERE (CRITICAL)
    # --------------------------------------------------
    status = output_json.get("run_status", {}).get("status", "unknown")
    output_json = ensure_complete_metrics(output_json, status)
    if run_status["status"] != "solved":
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
