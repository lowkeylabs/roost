# src/owlroost/domain/lever.py

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING

import numpy as np
from owlplanner.config.plan_bridge import config_to_plan

if TYPE_CHECKING:
    from ..models.case import Case

# ==========================================================
# Lever Summary
# ==========================================================


@dataclass
class LeverSummary:
    retirement_horizon: int | None = None
    max_spending: float | None = None
    first_year_total_withdrawals: float | None = None


# ==========================================================
# Helpers
# ==========================================================


def _normalized_raw(case: Case) -> dict:
    """
    Return a deep-copied raw config with HFP normalized.

    If HFP file does not exist, convert to "None" so OWL
    does not raise FileNotFoundError.
    """
    raw = deepcopy(case._raw_dict)

    dirname = case.path.parent
    hfp_section = raw.get("household_financial_profile", {})
    hfp_name = hfp_section.get("HFP_file_name")

    if hfp_name and hfp_name != "None":
        hfp_path = dirname / hfp_name
        if not hfp_path.exists():
            raw.setdefault("household_financial_profile", {})
            raw["household_financial_profile"]["HFP_file_name"] = "None"

    return raw


def _has_valid_hfp(case: Case) -> bool:
    """
    Returns True only if HFP exists and file is present.
    """
    dirname = case.path.parent
    hfp_name = case._raw_dict.get("household_financial_profile", {}).get("HFP_file_name")

    if not hfp_name or hfp_name == "None":
        return False

    return (dirname / hfp_name).exists()


# ==========================================================
# Retirement Horizon
# ==========================================================


def compute_retirement_horizon(case: Case) -> int | None:
    """
    Returns:
        0      → already retired (no HFP or no wages)
        N      → retires in N years
        None   → never retires
    """

    # No HFP → already retired
    if not _has_valid_hfp(case):
        return 0

    import pandas as pd

    raw = _normalized_raw(case)
    dirname = case.path.parent

    plan = config_to_plan(
        raw,
        dirname=str(dirname),
        loadHFP=True,
        logstreams=[StringIO(), StringIO()],
        verbose=False,
    )

    retirement_years = []

    hfp_name = raw["household_financial_profile"]["HFP_file_name"]
    hfp_path = dirname / hfp_name

    for iname in plan.inames:
        sheet = pd.read_excel(hfp_path, sheet_name=iname)

        projection_length = len(sheet) - 5
        df = plan.timeLists[iname]
        projection = df.iloc[5 : 5 + projection_length]

        wages = projection["anticipated wages"].tolist()

        # Already retired
        if all(w == 0 for w in wages):
            retirement_years.append(0)
            continue

        seen_positive = False
        retirement_index = None

        for idx, w in enumerate(wages):
            if w > 0:
                seen_positive = True
            elif seen_positive and w == 0:
                retirement_index = idx
                break

        if retirement_index is None:
            return None

        retirement_years.append(retirement_index)

    return max(retirement_years) if retirement_years else None


# ==========================================================
# Max Spending (Zero Bequest)
# ==========================================================


def compute_spending_and_more(case: Case) -> tuple[float | None, float | None]:
    """
    Solve plan with zero bequest objective and return
    max sustainable first-year net spending.

    Works even without HFP.
    """

    raw = _normalized_raw(case)
    dirname = case.path.parent

    # Force correct optimization configuration
    raw.setdefault("optimization_parameters", {})
    raw["optimization_parameters"]["objective"] = "maxSpending"

    raw.setdefault("solver_options", {})
    raw["solver_options"]["bequest"] = 0
    raw["solver_options"].pop("netSpending", None)

    plan = config_to_plan(
        raw,
        dirname=str(dirname),
        loadHFP=True,
        verbose=False,
        logstreams=[StringIO(), StringIO()],
    )

    plan.solve(plan.objective, plan.solverOptions)

    if getattr(plan, "caseStatus", None) != "solved":
        return None, None

    max_spending = None
    withdrawals = None

    if hasattr(plan, "g_n") and len(plan.g_n) > 0:
        max_spending = float(plan.g_n[0])

    if hasattr(plan, "w_ijn"):
        w = np.sum(plan.w_ijn, axis=(0, 1))
        if len(w) > 0:
            withdrawals = float(w[0])

    return max_spending, withdrawals


# ==========================================================
# Combined Lever Summary
# ==========================================================


def compute_levers(case: Case) -> LeverSummary:
    max_spend, withdrawals = compute_spending_and_more(case)
    return LeverSummary(
        retirement_horizon=compute_retirement_horizon(case),
        max_spending=max_spend,
        first_year_total_withdrawals=withdrawals,
    )
